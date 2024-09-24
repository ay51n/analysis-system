# Customer Conversation Keyword & Brand Extractor

This repository contains a Python script that processes customer conversations, extracts keywords, identifies brands, and categorizes product types using natural language processing (NLP). The extracted information is stored in MongoDB for further analysis and reference.

## Features
- **Keyword Extraction**: Extracts meaningful keywords (nouns, verbs, adjectives, numbers) from customer messages.
- **Brand Recognition**: Identifies brands mentioned in the conversations based on predefined mappings.
- **Product Categorization**: Classifies extracted keywords into predefined product categories.
- **MongoDB Integration**: Updates and stores processed conversation data in a MongoDB database.
- **Continuous Monitoring**: The script can be set up to monitor and process new conversations in real-time.

## Technologies Used
- **Python**
- **SpaCy**: For natural language processing and keyword extraction.
- **MongoDB**: For storing and managing conversation data.
- **Logging**: To track the flow of the script and errors if any.
- **Datetime**: For handling timestamps in conversation events.

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/conversation-keyword-extractor.git
