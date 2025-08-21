import requests
from bs4 import BeautifulSoup
import sys
import logging
import json
import re
from requests.exceptions import RequestException
from urllib3.exceptions import HTTPError
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log')
    ]
)
logger = logging.getLogger(__name__)

def normalize_title(title):
    """Normalize title for easier comparison"""
    if not title:
        return ''
    
    # Convert to lowercase, remove dots and spaces
    normalized = title.lower().replace('.', '').replace(' ', '')
    
    # Special case handling for various move notations
    if normalized in ['66l', '66m', '66h']:
        # Handle dash notation without spaces
        return normalized
    elif normalized in ['5u', '4u', '2u', 'ju']:  # Add directional U moves
        # Keep directional notation as is
        return normalized
    elif re.match(r'^[1-9][lmhu]$', normalized):  # Handle any directional normal
        # Keep directional notation as is
        return normalized
    elif normalized.startswith('j') and len(normalized) > 1:  # Handle jump moves
        # Keep jump notation as is
        return normalized
    elif re.match(r'^[0-9]+[lmhu]$', normalized):  # Handle special move notations like 236L
        # Keep special move notation as is
        return normalized
    
    # For special moves, try to match common patterns
    if 'dream attraction' in normalized or 'dream come true' in normalized:
        return '236l'
    elif 'rodent rhythm' in normalized:
        return '623l'
    elif 'ring the dormouse' in normalized:
        return '214l'
    elif 'marching teeth' in normalized:
        return '22l'
    elif 'ultimate dream attraction' in normalized:
        return '236u'
    elif 'ultimate rodent rhythm' in normalized:
        return '623u'
    elif 'ultimate ring the dormouse' in normalized:
        return '214u'
    elif 'ultimate marching teeth' in normalized:
        return '22u'
    elif 'gilded heaven strike' in normalized:
        return '236236h'
    elif 'eccentrical parade' in normalized:
        return '236236u'
    
    return normalized

def find_move_section(soup, section_name, subsection_name):
    """Find a specific section and subsection in the HTML"""
    logger.debug(f"Looking for section '{section_name}' and subsection '{subsection_name}'")
    
    # Normalize the subsection name for comparison
    normalized_subsection = normalize_title(subsection_name)
    logger.debug(f"Normalized subsection name: {normalized_subsection}")
    
    # Find the section header
    section_header = None
    for h2 in soup.find_all('h2', class_='citizen-section-heading'):
        if normalize_title(h2.text) == normalize_title(section_name):
            section_header = h2
            break
    
    if not section_header:
        logger.error(f"Section '{section_name}' not found")
        return None
    
    # Get the section content
    section_content = None
    next_sibling = section_header.find_next_sibling()
    if next_sibling and next_sibling.name == 'section':
        section_content = next_sibling
    else:
        # Try to find the content in the parent div
        parent = section_header.parent
        if parent and parent.name == 'div':
            section_content = parent
    
    if not section_content:
        logger.error(f"Could not find section content for '{section_name}'")
        return None
    
    # Find all possible headers (h3, h4, h5) in this section
    all_headers = []
    for tag in ['h3', 'h4', 'h5']:
        all_headers.extend(section_content.find_all(tag))
    
    logger.debug(f"Found {len(all_headers)} possible move headers")
    
    # Try to find the specific move subsection with exact or normalized match
    target_header = None
    for header in all_headers:
        header_text = header.text.strip()
        
        # Debug log each header we check
        logger.debug(f"Checking header: '{header_text}' normalized as '{normalize_title(header_text)}'")
        
        # Special case for special moves like 236L
        if normalized_subsection in ['236l', '236m', '236h', '214l', '214m', '214h', '623l', '623m', '623h', '22l', '22m', '22h']:
            # Check if header contains the move notation
            if normalized_subsection in normalize_title(header_text):
                target_header = header
                logger.debug(f"Found special move match: {header_text}")
                break
            
            # Check for move name matches
            if normalized_subsection in ['236l', '236m', '236h'] and ('dream attraction' in header_text.lower() or 'dream come true' in header_text.lower()):
                target_header = header
                logger.debug(f"Found Dream Attraction/Dream Come True match: {header_text}")
                break
            elif normalized_subsection in ['623l', '623m', '623h'] and 'rodent rhythm' in header_text.lower():
                target_header = header
                logger.debug(f"Found Rodent Rhythm match: {header_text}")
                break
            elif normalized_subsection in ['214l', '214m', '214h'] and 'ring the dormouse' in header_text.lower():
                target_header = header
                logger.debug(f"Found Ring the Dormouse match: {header_text}")
                break
            elif normalized_subsection in ['22l', '22m', '22h'] and 'marching teeth' in header_text.lower():
                target_header = header
                logger.debug(f"Found Marching Teeth match: {header_text}")
                break
        else:
            # Normal case - check for exact or normalized match
            if header_text == subsection_name or normalize_title(header_text) == normalized_subsection:
                target_header = header
                logger.debug(f"Found match: {header_text}")
                break
    
    if not target_header:
        logger.error(f"Subsection '{subsection_name}' not found in '{section_name}'")
        return None
    
    # Find the attack container for this move
    attack_container = target_header.find_next('div', class_='attack-container')
    if not attack_container:
        logger.error(f"Could not find attack container for '{subsection_name}'")
        
        # Try a different approach - look for any div containing the move data
        # that follows the target header
        container = target_header.parent
        if container and container.name == 'div':
            attack_container = container
            logger.debug(f"Found alternative container for move data")
        else:
            # Look for any div following the header that might contain move data
            next_div = target_header.find_next('div')
            if next_div:
                attack_container = next_div
                logger.debug(f"Using next div as move container")
    
    return attack_container

def extract_frame_data(content):
    frame_data = {}
    data_div = content.find('div', class_='frameDataGrid')
    if data_div:
        # Get header names
        headers = []
        header_row = data_div.find('div', class_='frameDataGridHeader')
        if header_row:
            headers = [h.text.strip() for h in header_row.find_all('div')]
        
        # Get data values
        rows = data_div.find_all('div', class_='frameDataGridRow')
        if rows and len(rows) > 0:
            cells = rows[0].find_all('div')
            if len(cells) >= 8:
                frame_data = {
                    'Damage': cells[0].text.strip(),
                    'Guard': cells[1].text.strip(),
                    'Startup': cells[2].text.strip(),
                    'Active': cells[3].text.strip(),
                    'Recovery': cells[4].text.strip(),
                    'On-Block': cells[5].text.strip(),
                    'On-Hit': cells[6].text.strip(),
                    'Invuln': cells[7].text.strip()
                }
    
    # If we couldn't find the frame data grid, try an alternative approach
    if not frame_data and content:
        try:
            # Look for attack-info section
            attack_info = content.find('div', class_='attack-info')
            if attack_info:
                frame_data_section = attack_info.find('div', text=re.compile('Frame Data', re.IGNORECASE))
                if frame_data_section:
                    table = frame_data_section.find_next('table')
                    if table:
                        for row in table.find_all('tr'):
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                key = cells[0].text.strip()
                                value = cells[1].text.strip()
                                frame_data[key] = value
        except Exception as e:
            logger.error(f"Error in alternative frame data extraction: {str(e)}")
    
    return frame_data

def extract_frame_chart_data(content):
    chart_data = {}
    
    # First, try to find the total frames value directly from the span
    total_value_span = content.find('span', class_='frame-data-total-value')
    if total_value_span:
        chart_data['total_frames'] = total_value_span.text.strip()
        
    # Rest of the chart extraction remains the same
    chart_section = content.find('div', class_='frameChartSection')
    if chart_section:
        frame_chart = chart_section.find('div', class_='frameChart')
        if frame_chart:
            startup_div = frame_chart.find('div', class_='frameChart-startup')
            active_div = frame_chart.find('div', class_='frameChart-active')
            recovery_div = frame_chart.find('div', class_='frameChart-recovery')
            
            if startup_div:
                chart_data['startup_width'] = startup_div.get('style', '').split('width:')[1].split(';')[0].strip() if 'width:' in startup_div.get('style', '') else ''
            if active_div:
                chart_data['active_width'] = active_div.get('style', '').split('width:')[1].split(';')[0].strip() if 'width:' in active_div.get('style', '') else ''
            if recovery_div:
                chart_data['recovery_width'] = recovery_div.get('style', '').split('width:')[1].split(';')[0].strip() if 'width:' in recovery_div.get('style', '') else ''
            
            # If we didn't find the span directly earlier, try the older method
            if 'total_frames' not in chart_data:
                total_div = chart_section.find('div', class_='frame-data-total')
                if total_div:
                    total_span = total_div.find('span', class_='frame-data-total-value')
                    if total_span:
                        chart_data['total_frames'] = total_span.text.strip()
    
    return chart_data

def extract_additional_data(content):
    additional_data = {}
    
    # Look specifically for On-Counter Hit data
    attack_info = content.find('div', class_='attack-info')
    if attack_info:
        # Try to find counter hit info in different ways
        
        # Method 1: Look for elements containing "Counter Hit" text
        counter_hit_elements = attack_info.find_all(lambda tag: tag.name and tag.text and 'Counter Hit' in tag.text)
        for element in counter_hit_elements:
            # Try to find the value right after this element
            counter_value = element.find_next('div')
            if counter_value and counter_value.text.strip():
                # Extract just the numeric value with plus/minus sign
                value_text = counter_value.text.strip()
                # Look for patterns like +10, -5, etc.
                match = re.search(r'([+-]\d+)', value_text)
                if match:
                    additional_data['On-Counter Hit'] = match.group(1)
                    break
        
        # Method 2: Look for frame advantage data
        if 'On-Counter Hit' not in additional_data:
            frame_data_section = attack_info.find('div', class_='frameDataGrid')
            if frame_data_section:
                rows = frame_data_section.find_all('div', class_='frameDataGridRow')
                for row in rows:
                    cells = row.find_all('div')
                    if len(cells) >= 2 and 'Counter' in cells[0].text:
                        # Extract just the numeric value with plus/minus sign
                        value_text = cells[1].text.strip()
                        match = re.search(r'([+-]\d+)', value_text)
                        if match:
                            additional_data['On-Counter Hit'] = match.group(1)
                        else:
                            additional_data['On-Counter Hit'] = value_text
    
    return additional_data

def extract_overview(content):
    overview = []
    
    # Try to find the description/overview section
    attack_info = content.find('div', class_='attack-info-body')
    if attack_info:
        # Find the first paragraph which is usually the overview
        first_p = attack_info.find('p')
        if first_p:
            overview.append(extract_text_with_tooltips(first_p))
            logger.debug(f"Extracted paragraph: {overview[-1]}")
    
    return overview

def extract_usage(content):
    usage = []
    
    # Try to find the attack info body
    info_body = content.find('div', class_='attack-info-body')
    if info_body:
        # Process paragraphs and lists
        paragraphs_processed = set()  # Keep track of paragraphs we've already processed
        
        for element in info_body.children:
            if element.name == 'p':
                # Skip the first paragraph if it's already in overview
                if element == info_body.find('p') and len(paragraphs_processed) == 0:
                    paragraphs_processed.add(element)
                    continue
                
                # Check if we've already processed this paragraph
                if element in paragraphs_processed:
                    continue
                
                extracted = extract_text_with_tooltips(element)
                usage.append(('paragraph', extracted))
                paragraphs_processed.add(element)
                logger.debug(f"Extracted paragraph: {extracted}")
            elif element.name == 'ul':
                for li in element.find_all('li'):
                    extracted = extract_text_with_tooltips(li)
                    usage.append(('list', extracted))
                    logger.debug(f"Extracted list item: {extracted}")
    
    return usage

def extract_text_with_tooltips(element):
    result = []
    
    # Check if element is None
    if not element:
        return result
    
    # Helper function to clean text
    def clean_text(text):
        # Remove HTML/CSS classes and other unwanted content
        text = re.sub(r'\.mw-parser-output[^}]+}', '', text)
        text = re.sub(r'\.input-container[^}]+}', '', text)
        text = re.sub(r'\.delimiter-[^}]+}', '', text)
        text = re.sub(r'\.notation-color[^}]+}', '', text)
        text = re.sub(r'\.quantifier[^}]+}', '', text)
        # Remove any remaining CSS classes
        text = re.sub(r'\.[a-zA-Z-]+{[^}]+}', '', text)
        # Fix common word splits
        text = re.sub(r'\bfor\s+ced\b', 'forced', text)
        text = re.sub(r'\bperfor\s+med\b', 'performed', text)
        text = re.sub(r'\bU\s+niversal\b', 'Universal', text)
        text = re.sub(r'\bU\s+ses\b', 'Uses', text)
        return text.strip()
    
    # Process each child node
    for content in element.contents:
        if isinstance(content, str):
            if content.strip():  # Only add non-empty text
                cleaned_text = clean_text(content)
                if cleaned_text:  # Only add if there's text after cleaning
                    result.append(('text', cleaned_text))
        elif hasattr(content, 'name'):  # It's a tag
            if content.name == 'span' and 'tooltip' in content.get('class', []):
                # Get the tooltip text without its inner tooltip text
                tooltip_text = ''
                for c in content.contents:
                    if isinstance(c, str):
                        tooltip_text += c
                    elif c.name != 'span' or 'tooltiptext' not in c.get('class', []):
                        tooltip_text += c.get_text()
                
                tooltip_text = clean_text(tooltip_text)
                
                # Get the tooltip explanation
                tooltip_content = content.find('span', class_='tooltiptext')
                if tooltip_content:
                    tooltip_data = clean_text(tooltip_content.text)
                    # Store as tooltip with separate tooltip_text and tooltip_data
                    if tooltip_text:  # Only add if there's text after cleaning
                        result.append(('tooltip', tooltip_text, tooltip_data))
                elif tooltip_text:  # Only add if there's text after cleaning
                    result.append(('text', tooltip_text))
            elif content.name == 'span' and any(cls in content.get('class', []) for cls in [
                'colorful-text-1', 'colorful-text-2', 'colorful-text-3', 'colorful-text-4', 'colorful-text-7'
            ]):
                # These are move notations with colors
                cleaned_text = clean_text(content.text)
                if cleaned_text:  # Only add if there's text after cleaning
                    result.append(('move', cleaned_text))
            elif content.name == 'a':
                # Handle links to other moves
                cleaned_text = clean_text(content.text)
                if cleaned_text:  # Only add if there's text after cleaning
                    result.append(('move', cleaned_text))
            elif content.name == 'br':
                # Ignore line breaks
                continue
            else:
                # For any other tag, get its text
                cleaned_text = clean_text(content.get_text())
                if cleaned_text:  # Only add if there's text after cleaning
                    result.append(('text', cleaned_text))
    
    return result

def extract_images(content):
    """Extract both standard and hitbox images from content."""
    images = {
        'standard': None,
        'hitbox': None
    }
    
    # Try to find the attack gallery
    gallery = content.find('div', class_='attack-gallery')
    if gallery:
        # Find all tabber panels in the gallery (Images and Hitboxes tabs)
        tabber_panels = gallery.find_all('article', class_='tabber__panel')
        
        # Process each panel to find images
        for panel in tabber_panels:
            # Get panel ID to determine if it's the hitbox panel
            panel_id = panel.get('id', '')
            is_hitbox = 'Hitboxes' in panel_id
            
            # Find image in the panel
            img_tag = None
            figure = panel.find('figure')
            if figure:
                img_tag = figure.find('img')
            else:
                img_tag = panel.find('img')
                
            if img_tag and 'src' in img_tag.attrs:
                img_url = "https://www.dustloop.com" + img_tag['src']
                # Fix malformed URLs
                img_url = correct_image_url(img_url)
                # Convert thumbnail URL to full resolution
                if 'thumb' in img_url:
                    img_url = convert_thumbnail_to_full_res(img_url)
                
                # Assign to appropriate category
                if is_hitbox or 'Hitbox' in img_url:
                    images['hitbox'] = img_url
                else:
                    images['standard'] = img_url
    
    # If we couldn't find images in gallery, try looking elsewhere
    if not images['standard'] and not images['hitbox']:
        img_tags = content.find_all('img')
        for img_tag in img_tags:
            if 'src' in img_tag.attrs:
                img_url = "https://www.dustloop.com" + img_tag['src']
                # Fix malformed URLs
                img_url = correct_image_url(img_url)
                # Convert thumbnail URL to full resolution
                if 'thumb' in img_url:
                    img_url = convert_thumbnail_to_full_res(img_url)
                
                # Determine if this is a hitbox image or standard image
                if 'Hitbox' in img_url:
                    images['hitbox'] = img_url
                else:
                    images['standard'] = img_url
    
    return images

def convert_thumbnail_to_full_res(img_url):
    # For Dustloop wiki thumbnail URLs
    if '/thumb/' in img_url:
        # Extract the file path without the 'thumb' part
        parts = img_url.split('/thumb/')
        if len(parts) == 2:
            base = parts[0]
            path = parts[1]
            
            # Find position of last slash
            last_slash_pos = path.rfind('/')
            if last_slash_pos != -1:
                # Get everything after the last slash (which has thumbnail size)
                filename = path[last_slash_pos + 1:]
                
                # Remove size prefix if present (like '210px-')
                if '-' in filename and filename.split('-')[0].endswith('px'):
                    filename = filename.split('-', 1)[1]
                
                # Construct path without /thumb/ and without size prefix
                file_path = path[:last_slash_pos + 1] + filename
                return f"{base}/{file_path}"
    
    # If conversion failed or not needed, return original URL
    return img_url
    
def correct_image_url(url):
    # If URL ends with filename/filename.ext pattern, remove the last part
    parts = url.split('/')
    if len(parts) >= 2:
        last_part = parts[-1]
        second_last_part = parts[-2]
        
        # If the last part contains the second last part (duplicate filename issue)
        if second_last_part in last_part:
            # Remove the last part
            return url.rsplit('/', 1)[0]
    
    return url

def find_section_with_fallbacks(soup, section_name, subsection_name):
    """Try multiple section names to find the right content"""
    logger.debug(f"Attempting to find section with fallbacks for '{section_name}' and subsection '{subsection_name}'")
    
    # Try standard section name first
    content = find_move_section(soup, section_name, subsection_name)
    if content:
        return content
    
    # Fallback section names to try if the primary one doesn't work
    fallback_sections = []
    
    # If looking for dash normals, try these alternatives
    if section_name.lower() in ['dash normals', 'dashnormals']:
        fallback_sections = [
            'Dash Attacks',
            'Dash Moves',
            'Normal Moves',  # Some wikis include dash moves under normal moves
            'Normals',       # Another variation
            'Command Normals' # Another possible section name
        ]
    
    # Try each fallback section
    for fallback in fallback_sections:
        logger.debug(f"Trying fallback section: '{fallback}'")
        content = find_move_section(soup, fallback, subsection_name)
        if content:
            logger.debug(f"Found content using fallback section: '{fallback}'")
            return content
    
    # If that doesn't work, try searching for the subsection directly
    # This helps when dash moves are in a different section
    logger.debug("Trying to find subsection directly, regardless of section")
    
    # Normalize for comparison
    normalized_subsection = normalize_title(subsection_name)
    
    # Search all headers in the page for the subsection
    for tag in ['h3', 'h4', 'h5']:
        for header in soup.find_all(tag):
            header_text = header.text.strip()
            
            # Check for exact or normalized match with the subsection
            if (header_text == subsection_name or 
                normalize_title(header_text) == normalized_subsection or
                subsection_name.lower() in header_text.lower()):
                
                logger.debug(f"Found header matching subsection directly: '{header_text}'")
                
                # Find the attack container for this move
                attack_container = header.find_next('div', class_='attack-container')
                if attack_container:
                    logger.debug("Found attack container by direct subsection search")
                    return attack_container
                
                # Try parent div as fallback
                container = header.parent
                if container and container.name == 'div':
                    logger.debug("Found parent div as container by direct subsection search")
                    return container
    
    # Nothing found
    return None

def scrape_dustloop(character, section, subsection):
    url = f"https://www.dustloop.com/w/GBVSR/{character}"
    logger.info(f"Scraping data for {character} - {section} {subsection}")
    logger.debug(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)  # Add timeout
        response.raise_for_status()  # Raise exception for bad status codes
        
        if response.status_code == 404:
            logger.error(f"Character page not found: {url}")
            return {"error": f"Character '{character}' not found on Dustloop Wiki"}
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if page exists but is empty/redirect
        if soup.find(text=re.compile("There is currently no text in this page")):
            logger.error(f"Empty wiki page for character: {character}")
            return {"error": f"No data available for character '{character}'"}
        
        # Use the improved function to find move section with fallbacks
        content = find_section_with_fallbacks(soup, section, subsection)
        
        if not content:
            logger.error(f"Could not find content for {character}'s {section} {subsection}")
            return {"error": f"Move '{subsection}' not found in section '{section}' for {character}"}
        
        # Extract all the data
        try:
            frame_data = extract_frame_data(content)
            frame_chart = extract_frame_chart_data(content)
            additional_data = extract_additional_data(content)
            overview = extract_overview(content)
            usage = extract_usage(content)
            images = extract_images(content)
            
            # Validate that we got at least some data
            if not frame_data and not overview and not usage:
                logger.warning(f"No data extracted for {character}'s {subsection}")
                return {"error": f"No frame data or move information found for {character}'s {subsection}"}
            
            return {
                'frame_data': frame_data,
                'frame_chart': frame_chart,
                'additional_data': additional_data,
                'overview': overview,
                'usage': usage,
                'image_url': images['standard'],
                'hitbox_url': images['hitbox']
            }
            
        except Exception as e:
            logger.error(f"Error extracting data: {str(e)}", exc_info=True)
            return {"error": f"Error processing move data: {str(e)}"}
            
    except RequestException as e:
        logger.error(f"Request error: {str(e)}", exc_info=True)
        return {"error": "Failed to connect to Dustloop Wiki. Please try again later."}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {"error": "An unexpected error occurred. Please try again later."}

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(json.dumps({"error": "Usage: python script.py <character> <section> <subsection>"}))
        sys.exit(1)
    
    try:
        character, section, subsection = sys.argv[1:]
        result = scrape_dustloop(character, section, subsection)
        
        if result:
            print(json.dumps(result))
        else:
            print(json.dumps({"error": "Content not found"}))
    except Exception as e:
        logger.error(f"Script error: {str(e)}", exc_info=True)
        print(json.dumps({"error": "An unexpected error occurred while running the script"}))