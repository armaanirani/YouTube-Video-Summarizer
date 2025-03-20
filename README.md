# YouTube Summarizer 📝

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Demo](#demo)
- [Installation](#installation)
- [Dependencies](#dependencies)
- [Usage](#usage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Contact](#contact)

## Overview

### Description
YouTube Summarizer is an AI-powered tool that transforms lengthy YouTube videos into concise summaries, structured notes, and organized transcripts. Designed for students, researchers, and lifelong learners, it solves the problem of information overload by enabling efficient content consumption.

### Technology Stack
- **Frontend**: Streamlit
- **AI Engine**: Google Gemini
- **Backend**: Python 3.8+
- Key Libraries:
  - `youtube-transcript-api`
  - `google-generativeai`
  - `reportlab` (PDF generation)
  - `python-dotenv`

## Features

### 📜 Transcript Extraction
- Automatic detection of available captions
- Timestamp preservation
- Text normalization and cleaning
- Multiple display formats (plain text/timestamped table)

### 📊 Summary Generation
- **Concise**: 3-5 bullet points of key ideas (up to 250 words).
- **Detailed**: Paragraph-formatted comprehensive summary (up to 500 words).
- **Chapter-Based**: Time-stamped sections with headings (up to 500 words).
- **Study Notes**: Generates structured, actionable notes with sections like Introduction, Key Points, Action Items, Quotes, and Resources.

### 💾 Export Options
- Save as PDF with professional formatting
- Export as plain text files
- Clipboard copy functionality
- Automatic filename generation with metadata

### 🖥 User-Friendly Interface
- Intuitive URL input and processing
- Real-time progress indicators
- Responsive design for all devices
- Clear error messages and validations

## Demo

### Screenshots
1. **Main Interface**  
![Main Interface](https://via.placeholder.com/800x400.png?text=Video+Processing+Interface)

2. **Summary Example**  
![Summary Preview](https://via.placeholder.com/800x400.png?text=Generated+Summary)

3. **Export Options**  
![Export Menu](https://via.placeholder.com/800x400.png?text=Export+Options)

### Live Demo
[Try it Now!](https://your-streamlit-app-url.herokuapp.com) (Coming Soon)

## Installation

### Prerequisites
- Python 3.8+
- Google API key (Gemini AI)
- YouTube API key (optional)

### Setup
1. Clone repository:
   ```bash
   git clone https://github.com/yourusername/youtube-summarizer.git
   cd youtube-summarizer

2. Create virual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/MacOS
   venv\Scripts\activate  # Windows

3. Install dependencies:
   ```bash
   pip install -r requirements.txt

4. Create .env file:
   ```bash
   GOOGLE_API_KEY=your_actual_key
   YOUTUBE_API_KEY=your_optional_key

## Dependencies

The app relies on the following Python libraries:

Library | Purpose | Installation Command
--------|---------|---------------------
`streamlit` | Web app framework | `pip install streamlit`
`python-dotenv` | Load environment variables | `pip install python-dotenv`
`requests` | HTTP requests for API calls | `pip install requests`
`pillow` | Image processing (thumbnails) | `pip install pillow`
`google-generativeai` | Gemini AI integration | `pip install google-generativeai`
`youtube-transcript-api` | Extract YouTube transcripts | `pip install youtube-transcript-api`
`pandas` | Data handling (timestamped transcript) | `pip install pandas`
`reportlab` | PDF generation | `pip install reportlab`


## Usage

### Running the App
    streamlit run app.py
    

### Basic Workflow
1. Enter a valid public YouTube URL in the main text field
2. Click "Process Video"
3. Select desired tab (Summary/Notes/Transcript)
4. Choose output format and click generate
5. Expport using the buttons below generated content

### Exporting Content
1. **Text File**: Click "Save as txt" -> Generates text document link for download
2. **PDF**: "Save as PDF" -> Generates formatted PDF document link for download
3. **Clipboard**: Click "copy to clipboard" button -> Paste anywhere

## Configuration

### Environment Variables (API keys)
Set in the `.env` file or enter manually in the app's sidebar if not configured.

|Variable|Required|Purpose|
|--------|--------|-------|
|`GOOGLE_API_KEY`|Yes|Gemini AI access|
|`YOUTUBE_API_KEY`|No|Enhanced metadata|

### Gemini Model
- Default model: `gemini-1.5-pro`.
- Modify in the `generate_summary()` or `generate_chapter_summary()` functions if a different model is preferred.

### Transcript Preprocessing
The app removes filler words (e.g., "um", "uh") and extra spaces. Adjust the `preprocess_transcript()` funtion to change this behavior.

### Customization Options
1. Modify `prompts` dictionary in `app.py` for different summary styles
2. Adust PDF templates in `generate_pdf() function
3. Change UI elements in Streamlit configuration

## Troubleshooting

1. "Invalid YouTube URL" Error: Ensure the Url is in a supported format (e.g., `https://www.youtube.com/watch?v=VIDEO_ID` or `https://youtu.be/VIDEO_ID`).
2. "No Transcript Found": The video may not have captions. Check if manual or auto-generated captions are available for the video on YouTube.
3. API Key Issues: Verify that `GOOGLE_API_KEY` and `YOUTUBE_API_KEY` are correctly set in the `.env` file or entered in the sidebar.
4. App Not Loading: Confirm all dependencies are installed and Python version is 3.8+. Runn `streamlit run app.py` from the correct directory.

## Contributing

We welcome contributions to improve the YouTube Summarizer! **Before making any changes, please follow these steps:**

1. **Contact Maintainers**  
   Email [armaanirani@gmail.com](mailto:armaanirani@gmail.com) with:
   - Subject line: "Contribution Proposal: [Brief Description]"
   - Details about your proposed feature/bug fix
   - Your GitHub username

2. **Await Approval**  
   I’ll review your proposal within 3-5 business days and provide feedback/approval.

3. **Follow Development Guidelines**  
   Once approved:
   - Fork the repository
   - Create a feature branch:  
     ```bash 
     git checkout -b feature/your-feature-name
     ```
   - Implement changes with clear commit messages:
     ```bash
     git commit -m 'Added an amazing feature'
   - Test thoroughly
   - Push to your fork:  
     ```bash
     git push origin feature/your-feature-name
     ```
   - Open a Pull Request with a detailed description

### Code Standards
- Follow PEP8 conventions
- Include docstrings for all functions
- Use descriptive variable names
- Add comments for complex logic
- Ensure backward compatibility

---

## Contact

**Before contributing, please contact:**  
**Maintainer**: [Armaan Irani]  
**Email**: [armaanirani@gmail.com](mailto:armaanirani@gmail.com)  
**GitHub**: [@armaanirani](https://github.com/armaanirani)  

**Project Repository**:  
[https://github.com/armaanirani/youtube-summarizer](https://github.com/armaanirani/youtube-summarizer)  

**For Issues/Feedback**:  
- Open a ticket in [GitHub Issues](https://github.com/armaanirani/youtube-summarizer/issues)  
- Email with subject line "[YouTube Summarizer] - [Brief Topic]"  

**Note**: All contribution proposals must be emailed first for discussion. Unsolicited pull requests will not be accepted without prior coordination.  

---
