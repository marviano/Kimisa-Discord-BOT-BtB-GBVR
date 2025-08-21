import requests
from bs4 import BeautifulSoup
import sys
import logging
import json
import re

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def analyze_character_page(character):
    url = f"https://www.dustloop.com/w/GBVSR/{character}"
    logger.debug(f"Analyzing URL: {url}")
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all major sections (h2 headers)
    sections = {}
    
    for h2 in soup.find_all('h2'):
        section_name = h2.text.strip()
        
        if not section_name or section_name in ['Navigation', 'Contents']:
            continue
        
        # Get the section content
        section_content = h2.find_next('section')
        if not section_content:
            # Try alternative approach for content
            next_h2 = h2.find_next('h2')
            if next_h2:
                # Get all elements between this h2 and the next
                section_elements = []
                current = h2.next_sibling
                while current and current != next_h2:
                    section_elements.append(current)
                    current = current.next_sibling
                
                # Create a wrapper for these elements
                from bs4 import BeautifulSoup
                section_content = BeautifulSoup("<div></div>", "html.parser").div
                for element in section_elements:
                    section_content.append(element)
        
        # Skip if no content found
        if not section_content:
            sections[section_name] = []
            continue
        
        # Find all possible move headers in this section
        moves = []
        for tag in ['h3', 'h4', 'h5']:
            for header in section_content.find_all(tag):
                move_name = header.text.strip()
                if move_name and not re.match(r'^[0-9.]+$', move_name):  # Skip numeric headers
                    moves.append(move_name)
        
        sections[section_name] = moves
    
    return sections

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python script.py <character>"}))
        sys.exit(1)
    
    character = sys.argv[1]
    try:
        sections = analyze_character_page(character)
        print(json.dumps(sections))
    except Exception as e:
        print(json.dumps({"error": str(e)}))