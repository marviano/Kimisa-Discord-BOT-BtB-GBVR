const { Client, GatewayIntentBits, EmbedBuilder, ActivityType } = require('discord.js');
require('dotenv').config();
const { exec } = require('child_process');

// Add cooldown handling
const cooldowns = new Map();
const COOLDOWN_DURATION = 3000; // 3 seconds cooldown

const client = new Client({ 
    intents: [
        GatewayIntentBits.Guilds, 
        GatewayIntentBits.GuildMessages, 
        GatewayIntentBits.MessageContent
    ] 
});

client.once('ready', () => {
    console.log('Bot is online!');
    
    // Set bot status
    client.user.setPresence({
        activities: [{ 
            name: '!kimi help | GBVSR Frame Data', 
            type: ActivityType.Playing 
        }],
        status: 'online',
    });
});

// Valid characters list
const validCharacters = [
    'Gran', 'Djeeta', 'Katalina', 'Charlotta', 'Lancelot', 'Ferry',
    'Lowain', 'Ladiva', 'Percival', 'Metera', 'Zeta', 'Vasaraga',
    'Beelzebub', 'Narmaya', 'Soriz', 'Djeeta', 'Belial', 'Cagliostro',
    'Yuel', 'Uno', 'Six', 'Seox', 'Siegfried', 'Vira', 'Avatar Belial',
    'Anre', 'Seofon', 'Tweyen', 'Threo', 'Feower', 'Fif', 'Seox',
    'Seofon', 'Nio', 'Eahta', 'Id'
];

const scrapeSpecificSection = (character, section, subsection) => {
    return new Promise((resolve, reject) => {
        const pythonPath = 'C:\\Users\\Austin\\AppData\\Local\\Programs\\Python\\Python311\\python.exe';
        exec(`"${pythonPath}" scraper.py ${character} "${section}" "${subsection}"`, (error, stdout, stderr) => {
            if (error) {
                console.error(`Execution error: ${error.message}`);
                reject(`Error: ${error.message}`);
                return;
            }
            
            console.log(`Python script full stdout:\n${stdout}`);
            if (stderr) {
                console.error(`Python script stderr:\n${stderr}`);
            }
            
            resolve({ stdout, stderr });
        });
    });
};

// Helper function to generate visual frame bars
function getFrameBars(numFrames) {
    if (isNaN(numFrames) || numFrames <= 0) return '▯';
    
    // Cap the number of bars at 15 to avoid overly long messages
    const maxBars = 15;
    if (numFrames > maxBars) {
        return `▮${"▮".repeat(maxBars - 2)}▮ (${numFrames})`;
    }
    
    return "▮".repeat(numFrames);
}

// Format text with tooltips, moves, etc.
const formatTextWithTooltips = (textData) => {
    if (!textData || !Array.isArray(textData)) {
        return String(textData || '');
    }
    
    let formattedText = '';
    let glossaryItems = [];
    let isLinksList = false;
    
    // Check if this is a "Links into:" list
    if (Array.isArray(textData) && textData.length > 0) {
        for (const item of textData) {
            if (Array.isArray(item) && item[0] === 'text' && item[1].includes('Links into')) {
                isLinksList = true;
                break;
            }
        }
    }
    
    textData.forEach(item => {
        if (!Array.isArray(item)) {
            // Clean any HTML/CSS classes from plain text
            const cleanText = String(item || '').replace(/\.mw-parser-output[^}]+}/g, '');
            formattedText += cleanText;
            return;
        }
        
        const type = item[0];
        
        if (type === 'text') {
            // Clean any HTML/CSS classes from text content
            let cleanText = item[1].replace(/\.mw-parser-output[^}]+}/g, '');
            
            // First, protect move notations and special terms by adding markers around them
            cleanText = cleanText.replace(/(\d[LMHU])/g, '§$1§'); // Mark numbered moves
            cleanText = cleanText.replace(/([jc]\.[LMHU])/g, '§$1§'); // Mark j. and c. moves
            cleanText = cleanText.replace(/\b([LMHU])\b/g, '§$1§'); // Mark single button moves
            cleanText = cleanText.replace(/(Guard|Startup|Recovery|Advantage|Mid|High|Low)/g, '§$1§'); // Mark move data terms
            
            // Fix common word splits
            cleanText = cleanText.replace(/\bfor\s+ced\b/g, 'forced');
            cleanText = cleanText.replace(/\bperfor\s+med\b/g, 'performed');
            cleanText = cleanText.replace(/\bU\s+niversal\b/g, 'Universal');
            cleanText = cleanText.replace(/\bU\s+ses\b/g, 'Uses');
            
            // Handle bullet points and special characters
            cleanText = cleanText.replace(/•/g, '\n• '); // Add newline and space after bullet points
            cleanText = cleanText.replace(/ⓘ/g, 'ⓘ '); // Add space after info icon
            
            // Add spaces around specific words and punctuation
            cleanText = cleanText.replace(/Pressing/g, 'Pressing '); // Add space after "Pressing"
            cleanText = cleanText.replace(/activates/g, 'activates '); // Add space after "activates"
            cleanText = cleanText.replace(/\bor\b/g, ' or '); // Add spaces around "or"
            cleanText = cleanText.replace(/([,.])/g, '$1 '); // Add space after commas and periods
            
            // Fix move notation lists (like L,M,H)
            cleanText = cleanText.replace(/§([LMHU])§\s*,\s*§([LMHU])§\s*,\s*§([LMHU])§/g, '§$1,$2,$3§');
            
            // Remove unwanted spaces that might have been added within words
            cleanText = cleanText.replace(/(?<=[a-z])\s+(?=[a-z])/g, ''); // Remove spaces between lowercase letters
            
            // Restore move notations and ensure proper spacing around them
            cleanText = cleanText.replace(/§([^§]+)§/g, ' $1 '); // Add spaces around move notations
            
            // Clean up multiple spaces and trim
            cleanText = cleanText.replace(/\s+/g, ' '); // Normalize spaces
            cleanText = cleanText.trim(); // Trim any leading/trailing spaces
            
            // Ensure proper spacing around move data
            cleanText = cleanText.replace(/(Guard|Startup|Recovery|Advantage)\s+([A-Z])/g, '$1 $2');
            cleanText = cleanText.replace(/([A-Z])\s+(Mid|High|Low)/g, '$1 $2');
            
            formattedText += cleanText;
        } else if (type === 'tooltip') {
            const tooltipText = item[1];
            const tooltipData = item[2];
            
            // Clean any HTML/CSS classes from tooltip text
            const cleanTooltip = tooltipText.replace(/\.mw-parser-output[^}]+}/g, '');
            
            // Handle common tooltip suffixes like 's' correctly
            if (formattedText.endsWith(' ')) {
                formattedText += cleanTooltip;
            } else {
                formattedText += cleanTooltip;
            }
            
            // Collect glossary items for later use if needed
            if (tooltipData) {
                glossaryItems.push({ term: cleanTooltip, definition: tooltipData });
            }
        } else if (type === 'move') {
            // Clean any HTML/CSS classes from move text
            const cleanMove = item[1].replace(/\.mw-parser-output[^}]+}/g, '');
            if (isLinksList) {
                // In "Links into:" list, don't bold any moves
                formattedText += cleanMove;
            } else {
                // For other lists, bold the moves
                formattedText += `**${cleanMove}**`;
            }
        }
    });
    
    return formattedText;
};

// Split a single string with multiple bullet points into separate bullet points
const splitBulletPoints = (text) => {
    // If not a string, return as is
    if (typeof text !== 'string') {
        return [text];
    }
    
    // If no bullet points, return as is
    if (!text.includes('•')) {
        return [text];
    }
    
    // Normalize the text by ensuring spaces after each bullet point
    const normalized = text.replace(/•\s*/g, '• ');
    
    // Split by bullet points (•) and filter out empty parts
    const parts = normalized.split('• ').filter(part => part.length > 0);
    
    return parts;
};

const formatOutput = (character, subsection, data) => {
    console.log("Received data:", JSON.stringify(data, null, 2));
    
    // Format the main header with character and move name
    let output = `**${character} - ${subsection}**\n\n`;
    
    // Format Frame Data
    if (data.frame_data && Object.keys(data.frame_data).length > 0) {
        output += "**Frame Data**\n";
        for (const [key, value] of Object.entries(data.frame_data)) {
            output += `• ${key}: ${value}\n`;
        }
        output += "\n";
    }
    
    // Format Frame Chart - FIXED
    // Use the total frames from the website data
    let totalFrames;
    
    if (data.frame_chart && data.frame_chart.total_frames) {
        // Use the exact value from the website
        totalFrames = data.frame_chart.total_frames;
    } else {
        // Fall back to calculation but subtract 1 to match the game's actual value
        let startupFrames = parseInt(data.frame_data.Startup) || 0;
        let activeFrames = parseInt(data.frame_data.Active) || 0;
        let recoveryFrames = parseInt(data.frame_data.Recovery) || 0;
        totalFrames = (startupFrames + activeFrames + recoveryFrames - 1).toString();
    }
    
    output += `Total Frames: ${totalFrames}\n\n`;
    
    // Format Additional Properties - only include On-Counter Hit if it's a clean value
    if (data.additional_data && data.additional_data['On-Counter Hit']) {
        const counterHitValue = data.additional_data['On-Counter Hit'];
        // Only show the counter hit value if it's a simple numeric value
        if (/^[+-]?\d+$/.test(counterHitValue)) {
            output += "**Properties**\n";
            output += `• On-Counter Hit: ${counterHitValue}\n\n`;
        }
    }
    
    // Format Description & Usage
    output += "**Description & Usage**\n";
    
    // Combine overview and usage for better formatting
    const allContent = [];
    
    // First add overview paragraphs
    if (data.overview && data.overview.length > 0) {
        data.overview.forEach(paragraph => {
            allContent.push({
                type: 'paragraph',
                content: paragraph
            });
        });
    }
    
    // Then add usage information (bullet points, etc)
    if (data.usage && data.usage.length > 0) {
        data.usage.forEach(item => {
            // Always treat each list item as a separate list entry
            if (item[0] === 'list') {
                allContent.push({
                    type: 'list',
                    content: item[1]
                });
            } else if (item[0] === 'paragraph') {
                allContent.push({
                    type: item[0],
                    content: item[1]
                });
            }
        });
    }
    
    // Process all content with proper formatting
    let isFirstContentItem = true;
    let lastItemType = null;
    
    for (let i = 0; i < allContent.length; i++) {
        const item = allContent[i];
        const formattedText = formatTextWithTooltips(item.content);
        
        if (item.type === 'paragraph') {
            // Don't add a newline before the first paragraph
            if (!isFirstContentItem) {
                output += '\n';
            }
            output += formattedText;
            isFirstContentItem = false;
            lastItemType = 'paragraph';
        } else if (item.type === 'list') {
            // Add a newline before the first bullet point if needed
            if (!isFirstContentItem && lastItemType !== 'list') {
                output += '\n'; // Only one newline between paragraph and list
            } else if (lastItemType === 'list') {
                output += '\n'; // Add newline between bullet points
            }
            
            // Add bullet point without any bold formatting
            output += `• ${formattedText.trim()}`;
            
            isFirstContentItem = false;
            lastItemType = 'list';
        }
    }
    
    // Add a newline at the end to separate from the next section
    output += '\n';
    
    // Prepare embeds for the images
    const embeds = [];
    
    // Add standard image if available
    if (data.image_url) {
        embeds.push(new EmbedBuilder()
            .setTitle(`${character} - ${subsection}`)
            .setImage(data.image_url));
    }
    
    // Add hitbox image if available
    if (data.hitbox_url) {
        embeds.push(new EmbedBuilder()
            .setTitle(`${character} - ${subsection} (Hitbox)`)
            .setImage(data.hitbox_url));
    }
    
    console.log("Final formatted output:", output);
    return { content: output, embeds: embeds };
};

// Split message into chunks if it's too long for Discord
const splitMessage = (message, maxLength = 1900) => {
    if (!message || message.length <= maxLength) {
        return [message];
    }
    
    const chunks = [];
    const lines = message.split('\n');
    let currentChunk = '';
    
    lines.forEach(line => {
        // If adding this line would exceed the max length, push current chunk and start a new one
        if (currentChunk.length + line.length + 1 > maxLength) {
            chunks.push(currentChunk.trim());
            currentChunk = '';
        }
        
        currentChunk += line + '\n';
    });
    
    // Add the last chunk if there's anything left
    if (currentChunk) {
        chunks.push(currentChunk.trim());
    }
    
    return chunks;
};

// Normalize input to handle variations in command format
const normalizeInput = (input) => {
    // Common patterns for move notations
    const movePatterns = {
        // Normal moves
        'cl': 'c.L',
        'cm': 'c.M',
        'ch': 'c.H',
        'fl': 'f.L',
        'fm': 'f.M',
        'fh': 'f.H',
        '2l': '2L',
        '2m': '2M',
        '2h': '2H',
        '2u': '2U',
        'jl': 'j.L',
        'jm': 'j.M',
        'jh': 'j.H',
        'ju': 'j.U',
        '5l': '5L',
        '5m': '5M',
        '5h': '5H',
        '5u': '5U',
        '4u': '4U',
        '66l': '66L',
        '66m': '66M',
        '66h': '66H',
        '6l': '66L',
        '6m': '66M',
        '6h': '66H',
        'dashl': '66L',
        'dashm': '66M',
        'dashh': '66H',
        'dash l': '66L',
        'dash m': '66M',
        'dash h': '66H',
        
        // Vikala's special moves
        '236l': 'Dream Attraction',
        '236m': 'Dream Attraction',
        '236h': 'Dream Attraction',
        '236u': 'Ultimate Dream Attraction',
        '623l': 'Rodent Rhythm',
        '623m': 'Rodent Rhythm',
        '623h': 'Rodent Rhythm',
        '623u': 'Ultimate Rodent Rhythm',
        '214l': 'Ring the Dormouse',
        '214m': 'Ring the Dormouse',
        '214h': 'Ring the Dormouse',
        '214u': 'Ultimate Ring the Dormouse',
        '22l': 'Marching Teeth',
        '22m': 'Marching Teeth',
        '22h': 'Marching Teeth',
        '22u': 'Ultimate Marching Teeth',
        
        // Vikala's supers
        '236236h': 'Gilded Heaven Strike',
        '236236u': 'Eccentrical Parade'
    };
    
    // Normalize various command formats
    const normalized = input.toLowerCase()
        .replace(/\./g, '') // Remove dots
        .replace(/\s+/g, ''); // Remove spaces
    
    return movePatterns[normalized] || input;
};

client.on('messageCreate', async message => {
    if (message.author.bot) return;

    const content = message.content.toLowerCase();
    
    // Help command
    if (content === '!kimi help') {
        const helpEmbed = new EmbedBuilder()
            .setColor('#0099ff')
            .setTitle('Kimisa Bot - GBVSR Frame Data')
            .setDescription('Get frame data and move information from Dustloop Wiki')
            .addFields(
                { name: 'Basic Usage', value: '`!kimi <character> <section> <move>`' },
                { name: 'Sections', value: '`normal`, `dash`, `air`, `unique`, `skill`' },
                { name: 'Examples', value: '`!kimi Zeta normal c.L`\n`!kimi Gran dash 66H`\n`!kimi Charlotta air j.M`' },
                { name: 'Debug', value: '`!kimi-debug <character>` - Shows all available moves for a character' }
            )
            .setFooter({ text: 'Data sourced from Dustloop Wiki' });
        
        message.channel.send({ embeds: [helpEmbed] });
        return;
    }

    // Handle main kimi command
    if (content.startsWith('!kimi')) {
        // Check cooldown
        const userId = message.author.id;
        const now = Date.now();
        const cooldownEnd = cooldowns.get(userId);
        
        if (cooldownEnd && now < cooldownEnd) {
            const remainingTime = (cooldownEnd - now) / 1000;
            message.reply(`Please wait ${remainingTime.toFixed(1)} seconds before using this command again.`);
            return;
        }
        
        const args = message.content.split(' ');
        
        if (args.length < 3) {
            message.channel.send('Usage: !kimi <character> <section> <subsection>\nExample: !kimi Zeta normal c.L\nUse !kimi help for more information.');
            return;
        }
        
        // Set cooldown
        cooldowns.set(userId, now + COOLDOWN_DURATION);
        
        // Character handling (just capitalize first letter)
        let character = args[1];
        character = character.charAt(0).toUpperCase() + character.slice(1).toLowerCase();
        
        // Improved section mapping
        let sectionInput = args[2].toLowerCase();
        let section;
        
        // Map common section inputs to their proper form
        switch (sectionInput) {
            case 'normal':
                section = 'Normal Moves';
                break;
            case 'dash':
            case 'dashnormal':
            case 'dash_normal':
            case 'dash_normals':
                section = 'Dash Normals';
                break;
            case 'air':
            case 'airnormal':
            case 'air_normal':
            case 'air_normals':
                section = 'Air Normals';
                break;
            case 'unique':
            case 'uniqueaction':
            case 'unique_action':
                section = 'Unique Action';
                break;
            case 'skill':
            case 'skills':
                section = 'Skills';
                break;
            default:
                section = args[2]; // Keep original if no mapping found
        }
        
        let subsection = args.slice(3).join(' ');
        
        // Normalize subsection to handle different input formats
        subsection = normalizeInput(subsection);
        
        console.log(`Received command: !kimi ${character} ${section} ${subsection}`);
        
        // Send a "thinking" message to indicate the bot is working
        const loadingMessage = await message.channel.send(`Searching for ${character}'s ${subsection} move data...`);
        
        try {
            const { stdout, stderr } = await scrapeSpecificSection(character, section, subsection);
            
            // Delete the loading message
            try {
                await loadingMessage.delete();
            } catch (err) {
                console.error("Could not delete loading message:", err);
            }
            
            // If there's debug output, send it if we're in debug mode
            if (stderr && process.env.DEBUG_MODE === 'true') {
                console.error(`Debug information:\n${stderr}`);
                const debugChunks = splitMessage(stderr);
                for (const chunk of debugChunks) {
                    await message.channel.send(`Debug information:\n\`\`\`${chunk}\`\`\``);
                }
            }
            
            try {
                // Parse the JSON response from the Python script
                const result = JSON.parse(stdout);
                
                if (result.error) {
                    await message.channel.send(`Error: ${result.error}`);
                } else {
                    const { content, embeds } = formatOutput(character, subsection, result);
                    const chunks = splitMessage(content);
                    
                    // Send all text chunks first
                    for (let i = 0; i < chunks.length; i++) {
                        if (i < chunks.length - 1) {
                            await message.channel.send({
                                content: chunks[i]
                            });
                        }
                    }
                    
                    // Send the last text chunk with all the embeds
                    if (chunks.length > 0) {
                        await message.channel.send({
                            content: chunks[chunks.length - 1],
                            embeds: embeds
                        });
                    } else {
                        // If there's no text content, just send the embeds
                        await message.channel.send({
                            embeds: embeds
                        });
                    }
                }
            } catch (parseError) {
                console.error(`Error parsing JSON: ${parseError}`);
                console.error(`Problematic stdout: ${stdout}`);
                await message.channel.send(`An error occurred while processing the result. Error: ${parseError.message}`);
            }
        } catch (error) {
            console.error(`Error: ${error}`);
            await message.channel.send(`An error occurred: ${error}`);
            
            // Delete the loading message if it still exists
            try {
                await loadingMessage.delete();
            } catch (err) {
                console.error("Could not delete loading message:", err);
            }
        }
    }
    // Add the new debug command
    else if (content.startsWith('!kimi-debug')) {
        const args = content.split(' ');
        
        if (args.length < 2) {
            message.channel.send('Usage: !kimi-debug <character>');
            return;
        }
        
        let character = args[1];
        character = character.charAt(0).toUpperCase() + character.slice(1).toLowerCase();
        
        const loadingMessage = await message.channel.send(`Analyzing ${character}'s page structure...`);
        
        try {
            // Call a debug script that returns all sections and moves
            const pythonPath = 'C:\\Users\\Austin\\AppData\\Local\\Programs\\Python\\Python311\\python.exe';
            exec(`"${pythonPath}" scraper-debug.py ${character}`, async (error, stdout, stderr) => {
                // Delete loading message
                try {
                    await loadingMessage.delete();
                } catch (err) {
                    console.error("Could not delete loading message:", err);
                }
                
                if (error) {
                    await message.channel.send(`Error analyzing page: ${error.message}`);
                    return;
                }
                
                try {
                    const result = JSON.parse(stdout);
                    
                    if (result.error) {
                        await message.channel.send(`Error: ${result.error}`);
                    } else {
                        let output = `**${character}'s Move Structure**\n\n`;
                        
                        for (const [section, moves] of Object.entries(result)) {
                            output += `**${section}**\n`;
                            if (moves.length > 0) {
                                moves.forEach(move => {
                                    output += `• ${move}\n`;
                                });
                            } else {
                                output += "• No moves found\n";
                            }
                            output += "\n";
                        }
                        
                        // Split and send message if it's too long
                        const chunks = splitMessage(output);
                        for (const chunk of chunks) {
                            await message.channel.send(chunk);
                        }
                    }
                } catch (parseError) {
                    await message.channel.send(`Error processing results: ${parseError.message}`);
                }
            });
        } catch (error) {
            console.error(`Error: ${error}`);
            await message.channel.send(`An error occurred: ${error}`);
            
            try {
                await loadingMessage.delete();
            } catch (err) {
                console.error("Could not delete loading message:", err);
            }
        }
    }
});

client.login(process.env.TOKEN);