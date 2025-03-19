# YouTube Summarizer 📝

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Demo](#demo)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)
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
- **Concise**: 3-5 bullet points of key ideas
- **Detailed**: Paragraph-formatted comprehensive summary
- **Chapter-Based**: Time-stamped sections with headings
- **Study Notes**: Structured format with key points and resources

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
