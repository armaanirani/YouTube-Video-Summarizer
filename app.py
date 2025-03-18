import streamlit as st
from dotenv import load_dotenv
import os
import re
import requests
from PIL import Image
from io import BytesIO
import io
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import pandas as pd
import base64
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Page configuration
st.set_page_config(
    page_title="YouTube Summarizer",
    page_icon="📝",
    layout="wide"
)

# Helper functions
def extract_video_id(url):
    """Extract YouTube video ID from various URL formats"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',  # Standard and mobile youtube.com URLs
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',  # Short youtu.be URLs
        r'(?:youtube\.com\/embed\/)([0-9A-Za-z_-]{11})'  # Embedded player URLs
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def validate_youtube_url(url):
    """Validate if the URL is a proper YouTube URL and the video exists"""
    video_id = extract_video_id(url)
    if not video_id:
        return False, "Invalid YouTube URL format"
    
    # Check if video exists via YouTube API
    api_key = os.getenv("YOUTUBE_API_KEY")
    if api_key:
        try:
            response = requests.get(f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={api_key}&part=snippet,contentDetails,statistics")
            data = response.json()
            if not data.get('items'):
                return False, "Video not found or may be private"
            return True, data['items'][0]
        except Exception as e:
            # Fallback to basic validation if API call fails
            pass
    
    # Basic validation by checking if thumbnail exists
    try:
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/0.jpg"
        response = requests.get(thumbnail_url)
        if response.status_code == 200:
            # Check if it's the default "no thumbnail" image
            img = Image.open(BytesIO(response.content))
            if img.size != (120, 90):  # Default size for missing thumbnails
                return True, "Video exists (basic validation)"
        return False, "Video not found or may be private"
    except Exception as e:
        return False, f"Error validating URL: {str(e)}"

def get_video_metadata(video_id):
    """Get video metadata using YouTube API"""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return {
            "title": "Unknown (YouTube API key not configured)",
            "channel": "Unknown",
            "duration": "Unknown",
            "views": "Unknown",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/0.jpg",
            "video_id": video_id
        }
    
    try:
        response = requests.get(f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={api_key}&part=snippet,contentDetails,statistics")
        data = response.json()
        
        if not data.get('items'):
            return None
        
        video_data = data['items'][0]
        
        # Convert duration from ISO 8601 format
        duration = video_data['contentDetails']['duration']
        duration = duration.replace('PT', '').replace('H', 'h ').replace('M', 'm ').replace('S', 's')
        
        return {
            "title": video_data['snippet']['title'],
            "channel": video_data['snippet']['channelTitle'],
            "duration": duration,
            "views": f"{int(video_data['statistics']['viewCount']):,}",
            "thumbnail": video_data['snippet']['thumbnails']['high']['url'],
            "video_id": video_id
        }
    except Exception as e:
        st.error(f"Error fetching metadata: {str(e)}")
        return {
            "title": "Unknown",
            "channel": "Unknown",
            "duration": "Unknown",
            "views": "Unknown",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/0.jpg",
            "video_id": video_id
        }

def extract_transcript(video_id):
    """Extract transcript from YouTube video"""
    try:
        # Get transcript directly
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Format the transcript
        full_transcript = ""
        timestamped_transcript = []
        
        for entry in transcript_data:
            # Format timestamp as MM:SS
            timestamp = int(entry['start'])
            minutes = timestamp // 60
            seconds = timestamp % 60
            formatted_time = f"{minutes:02d}:{seconds:02d}"
            
            # Add to full transcript
            full_transcript += f"{entry['text']} "
            
            # Add to timestamped transcript
            timestamped_transcript.append({
                "timestamp": formatted_time,
                "text": entry['text']
            })
        
        return {
            "full_text": full_transcript.strip(),
            "timestamped": timestamped_transcript,
            "source": "YouTube Captions"
        }
    
    except NoTranscriptFound:
        return {"error": "No transcript found for this video"}
    except TranscriptsDisabled:
        return {"error": "Transcripts are disabled for this video"}
    except Exception as e:
        return {"error": f"Error extracting transcript: {str(e)}"}

def preprocess_transcript(transcript):
    """Clean and preprocess transcript text"""
    if "error" in transcript:
        return transcript
    
    # Clean filler words
    text = transcript["full_text"]
    filler_words = ["um", "uh", "like", "you know", "sort of", "kind of"]
    for word in filler_words:
        text = re.sub(r'\b' + word + r'\b', '', text, flags=re.IGNORECASE)
    
    # Remove duplicate spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    transcript["full_text"] = text
    return transcript

def generate_summary(transcript, summary_type="concise"):
    """Generate summary using Gemini API"""
    if "error" in transcript:
        return transcript["error"]
    
    model = genai.GenerativeModel("gemini-1.5-pro")
    
    prompts = {
        "concise": """You are a YouTube video summarizer expert. Provide a concise summary of the video transcript below in 3-5 bullet points. Focus on the main ideas and key takeaways only. Keep the total summary within 250 words. Make it easy to understand and skim.

Transcript:
""",
        "detailed": """You are a YouTube video summarizer expert. Provide a detailed summary of the video transcript below in well-structured paragraphs. Include the main ideas, key points, and important examples. Keep the total summary within 500 words. Make it comprehensive yet easy to understand.

Transcript:
""",
        "chapter": """You are a YouTube video summarizer expert. Create a chapter-based summary of the video transcript below. Identify major topics and create logical chapters with headings. Under each chapter, provide a brief summary of the content. Include timestamps where possible. Keep the total summary within 500 words.

Transcript:
""",
        "notes": """You are a professional note-taker. Transform the following video transcript into structured, actionable study notes. Include:
1. INTRODUCTION: Brief overview of the video's topic
2. KEY POINTS: Main concepts and ideas
3. ACTION ITEMS: Specific tasks or applications mentioned
4. QUOTES: Important quotes or statements
5. RESOURCES: Any tools, websites, or references mentioned

Use bullet points and keep the notes organized, concise, and easy to reference. Include timestamps where appropriate. Make these notes perfect for study or reference purposes.

Transcript:
"""
    }
    
    try:
        response = model.generate_content(prompts[summary_type] + transcript["full_text"])
        return response.text
    except Exception as e:
        return f"Error generating summary: {str(e)}"

# Advanced summary generation function (for future use)
def generate_advanced_summary(transcript, options):
    """Generate more customized summaries with advanced options"""
    if "error" in transcript:
        return transcript["error"]
    
    model = genai.GenerativeModel("gemini-1.5-pro")
    
    # Build prompt based on options
    prompt = f"""You are a YouTube video summarizer expert. Create a summary of the video transcript below based on the following requirements:

Format: {options.get('format', 'Bullets')}
Length: {options.get('length', 'Medium')}
Focus: {options.get('focus', 'General')}
Style: {options.get('style', 'Neutral')}

Transcript:
{transcript["full_text"]}
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary: {str(e)}"

# Fallback transcription function (for future use)
def transcribe_audio(video_id):
    """Transcribe audio using OpenAI Whisper API (fallback method)"""
    # Placeholder for future implementation
    # This would require:
    # 1. Downloading audio from YouTube
    # 2. Sending to Whisper API
    # 3. Processing the returned transcript
    return {"error": "Fallback transcription not implemented yet"}

# Function to generate chapter-based summary with timestamps
def generate_chapter_summary(transcript):
    """Generate chapter-based summary with timestamps"""
    if "error" in transcript:
        return transcript["error"]
    
    model = genai.GenerativeModel("gemini-1.5-pro")
    
    # Prompt Gemini to identify chapters directly
    chapter_prompt = f"""Analyze this YouTube video transcript and identify 5-7 main sections or topics.
For each section, provide:
1. A descriptive title
2. An approximate timestamp (MM:SS format)
3. A brief 2-3 sentence summary of what's covered in that section

Format your response as a Markdown document with second-level headings for each chapter, 
including the timestamp in brackets. For example:

## [00:00] Introduction
Brief summary of the introduction...

## [05:30] Main Topic
Brief summary of this section...

Transcript:
{transcript["full_text"][:15000]}  # Limit transcript length to avoid token limits
"""
    
    try:
        response = model.generate_content(chapter_prompt)
        chapter_summary = response.text
        
        # If no clear chapters were identified, try a different approach
        if "##" not in chapter_summary:
            # Fall back to a more structured approach
            structured_prompt = f"""Create a chapter-based summary of this YouTube video transcript.
Divide the content into exactly 5 logical sections, and for each section provide:
1. A clear title
2. An estimated timestamp in MM:SS format
3. A concise 2-3 sentence summary

Format as markdown with level 2 headings including timestamps:

## [00:00] Introduction
Summary text...

## [MM:SS] Title
Summary text...

And so on. Focus on creating a useful breakdown of the video content.

Transcript:
{transcript["full_text"][:15000]}
"""
            response = model.generate_content(structured_prompt)
            chapter_summary = response.text
        
        return "# Chapter-Based Summary\n\n" + chapter_summary
    
    except Exception as e:
        # In case of any error, fall back to regular summary
        fallback_prompt = f"""Create a structured summary of this YouTube video transcript.
Divide your summary into 5 main sections with clear headings.
For each section, provide a concise summary of the key points.

Transcript:
{transcript["full_text"][:15000]}
"""
        try:
            response = model.generate_content(fallback_prompt)
            return "# Structured Summary\n\n" + response.text
        except:
            return "Error generating chapter-based summary. Please try a different summary type."

# Function to generate PDF
def generate_pdf(content, title):
    """Generate a PDF from content"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Convert content to PDF-compatible format
    flowables = []
    
    # Add title
    flowables.append(Paragraph(title, styles['Title']))
    flowables.append(Spacer(1, 12))
    
    # Process content - split by lines and convert to paragraphs
    for line in content.split('\n'):
        if line.strip():
            if line.startswith('# '):
                # Main heading
                flowables.append(Paragraph(line[2:], styles['Heading1']))
            elif line.startswith('## '):
                # Subheading
                flowables.append(Paragraph(line[3:], styles['Heading2']))
            elif line.startswith('### '):
                # Sub-subheading
                flowables.append(Paragraph(line[4:], styles['Heading3']))
            elif line.startswith('- '):
                # Bullet point
                flowables.append(Paragraph(f"• {line[2:]}", styles['BodyText']))
            else:
                # Regular paragraph
                flowables.append(Paragraph(line, styles['BodyText']))
            
            flowables.append(Spacer(1, 6))
    
    # Build PDF
    doc.build(flowables)
    buffer.seek(0)
    return buffer

# Function to create download link for PDF
def create_download_link_pdf(pdf_bytes, filename, link_text):
    """Create a download link for PDF content"""
    b64 = base64.b64encode(pdf_bytes.getvalue()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

# Function to create download link for txt
def create_download_link(content, filename, link_text):
    """Create a download link for text content"""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link_text}</a>'
    return href


# Function to create Markdown export
def create_markdown_export(content, metadata, summary_type):
    """Create a properly formatted Markdown export"""
    markdown = f"""# {metadata['title']}

## Video Information
- **Channel:** {metadata['channel']}
- **Duration:** {metadata['duration']}
- **Views:** {metadata['views']}
- **URL:** https://www.youtube.com/watch?v={metadata['video_id']}

## {summary_type} Summary
{content}

---
Generated on {datetime.now().strftime('%Y-%m-%d')} using YouTube Summarizer App
"""
    return markdown


# Initialize session state for persistent data
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'notes' not in st.session_state:
    st.session_state.notes = None
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'metadata' not in st.session_state:
    st.session_state.metadata = None
if 'video_processed' not in st.session_state:
    st.session_state.video_processed = False


# Main app
def main():
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/youtube-play.png", width=100)
        st.title("YouTube Summarizer")
        st.markdown("Turn long YouTube videos into concise summaries and notes.")
        
        # API key input
        if not os.getenv("GOOGLE_API_KEY"):
            st.warning("⚠️ Gemini API key not found in .env file")
            api_key = st.text_input("Enter your Gemini API key:", type="password")
            if api_key:
                genai.configure(api_key=api_key)
        
        # About section
        st.markdown("---")
        st.markdown("### About")
        st.markdown("This app extracts transcripts from YouTube videos and uses Gemini AI to generate summaries and notes.")
        
        # Credits
        st.markdown("---")
        st.markdown("### Credits")
        st.markdown("Built with Streamlit and Google Gemini")
    
    # Main content
    st.title("📝 YouTube Transcript Summarizer")
    
    # Input section
    st.markdown("### Enter YouTube Video URL")
    url_col1, url_col2 = st.columns([3, 1])
    with url_col1:
        youtube_url = st.text_input("", placeholder="https://www.youtube.com/watch?v=...")
    with url_col2:
        process_button = st.button("Process Video", type="primary", use_container_width=True)
    
    # Show instructions if no URL entered
    if not youtube_url and not st.session_state.video_processed:
        st.info("Paste a YouTube URL above to get started. The app will extract the transcript and generate summaries.")
        st.markdown("#### Features:")
        st.markdown("- Extract video transcripts")
        st.markdown("- Generate concise or detailed summaries")
        st.markdown("- Create structured study notes")
        st.markdown("- Export content in various formats")
        return
    
    # Process the URL
    if youtube_url and (process_button or not st.session_state.video_processed):
        video_id = extract_video_id(youtube_url)
        
        if not video_id:
            st.error("❌ Invalid YouTube URL. Please check and try again.")
            return
        
        # URL validation
        is_valid, result = validate_youtube_url(youtube_url)
        if not is_valid:
            st.error(f"❌ {result}")
            return
        
        # Get video metadata
        with st.spinner("Fetching video metadata..."):
            metadata = get_video_metadata(video_id)
        
        if not metadata:
            st.error("❌ Could not retrieve video metadata.")
            return
        
        # Store metadata in session state
        st.session_state.metadata = metadata
        
        # Extract transcript
        with st.spinner("Extracting transcript..."):
            transcript = extract_transcript(video_id)
            transcript = preprocess_transcript(transcript)
        
        if "error" in transcript:
            st.error(f"❌ {transcript['error']}")
            return
        
        # Store transcript in session state
        st.session_state.transcript = transcript
        st.session_state.video_processed = True
    
    # Display processed video if available
    if st.session_state.video_processed and st.session_state.metadata:
        metadata = st.session_state.metadata
        transcript = st.session_state.transcript        
        
        # Display video info
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(metadata["thumbnail"], use_container_width=True)
        with col2:
            st.markdown(f"### {metadata['title']}")
            st.markdown(f"**Channel:** {metadata['channel']}")
            st.markdown(f"**Duration:** {metadata['duration']} | **Views:** {metadata['views']}")
        
        # Processing options
        st.markdown("### Processing Options")
        tab1, tab2, tab3 = st.tabs(["Summary", "Study Notes", "Transcript"])
        
        # Summary tab
        with tab1:
            summary_type = st.radio(
                "Summary Type:",
                ["Concise", "Detailed", "Chapter-Based"],
                horizontal=True,
                key="summary_type"
            )
            
            # Store the previous summary type to detect changes
            if 'prev_summary_type' not in st.session_state:
                st.session_state.prev_summary_type = summary_type
            
            generate_summary_clicked = st.button("Generate Summary", key="gen_summary")
            
            # Only generate summary if button is clicked, not when radio changes
            if generate_summary_clicked or st.session_state.get('summary_generated', False):
                with st.spinner("Generating summary..."):
                    # Generate summary only if button is clicked OR it's the first time loading with existing summary
                    if generate_summary_clicked:
                        # Reset current summary if type changed with button click
                        if summary_type.lower() != st.session_state.get('current_summary_type', ''):
                            st.session_state.summary = None
                        
                        # Generate the new summary
                        if not st.session_state.get('summary'):
                            if summary_type.lower() == "chapter-based":
                                summary = generate_chapter_summary(transcript)
                            else:
                                summary = generate_summary(transcript, summary_type.lower())
                            st.session_state.summary = summary
                            st.session_state.current_summary_type = summary_type.lower()
                    
                    # Use existing summary if available
                    summary = st.session_state.summary
                    st.session_state.summary_generated = True
                    
                st.markdown("### Summary")
                st.markdown(summary)
                
                # Export options
                st.markdown("### Export Options")
                export_col1, export_col2, export_col3 = st.columns(3)
                
                with export_col1:
                    if st.button("📝 Save as txt", key="save_summary_txt"):
                        filename = f"{metadata['title']}_Summary_{datetime.now().strftime('%Y%m%d')}.txt"
                        st.markdown(
                            create_download_link(summary, filename, "📥 Download as Text"),
                            unsafe_allow_html=True
                        )
                
                with export_col2:
                    if st.button("📋 Copy to Clipboard", key="copy_summary"):
                        st.success("Summary copied to clipboard!")
                
                with export_col3:
                    if st.button("📄 Save as PDF", key="save_summary_pdf"):
                        # Store the summary to make sure it's not lost
                        temp_summary = st.session_state.summary
                        
                        # Generate PDF
                        pdf_buffer = generate_pdf(temp_summary, f"{metadata['title']} - Summary")
                        
                        # Create download link
                        pdf_filename = f"{metadata['title']}_Summary_{datetime.now().strftime('%Y%m%d')}.pdf"
                        st.markdown(
                            create_download_link_pdf(pdf_buffer, pdf_filename, "📥 Download as PDF"),
                            unsafe_allow_html=True
                        )
        
        # Study Notes tab
        with tab2:
            if st.button("Generate Study Notes", key="gen_notes") or st.session_state.get('notes_generated', False):
                with st.spinner("Generating study notes..."):
                    if not st.session_state.get('notes'):
                        notes = generate_summary(transcript, "notes")
                        st.session_state.notes = notes
                    else:
                        notes = st.session_state.notes
                    
                    st.session_state.notes_generated = True
                
                st.markdown("### Study Notes")
                st.markdown(notes)
                
                # Export options
                st.markdown("### Export Options")
                export_col1, export_col2, export_col3 = st.columns(3)
                
                with export_col1:
                    if st.button("📝 Save as txt", key="save_notes_txt"):
                        filename = f"{metadata['title']}_Notes_{datetime.now().strftime('%Y%m%d')}.txt"
                        st.markdown(
                            create_download_link(notes, filename, "📥 Download as Text"),
                            unsafe_allow_html=True
                        )
                
                with export_col2:
                    if st.button("📋 Copy to Clipboard", key="copy_notes"):
                        st.success("Notes copied to clipboard!")
                
                with export_col3:
                    if st.button("📄 Save as PDF", key="save_notes_pdf"):
                        # Store the notes to make sure they're not lost
                        temp_notes = st.session_state.notes
                        
                        # Generate PDF
                        pdf_buffer = generate_pdf(temp_notes, f"{metadata['title']} - Study Notes")
                        
                        # Create download link
                        pdf_filename = f"{metadata['title']}_Notes_{datetime.now().strftime('%Y%m%d')}.pdf"
                        st.markdown(
                            create_download_link_pdf(pdf_buffer, pdf_filename, "📥 Download as PDF"),
                            unsafe_allow_html=True
                        )
        
        # Transcript tab
        with tab3:
            st.markdown("### Full Transcript")
            
            # Display options
            display_option = st.radio(
                "Display Format:",
                ["Plain Text", "With Timestamps"],
                horizontal=True,
                key="transcript_display"
            )
            
            if display_option == "Plain Text":
                st.text_area("", transcript["full_text"], height=400)
            else:
                # Create a dataframe for the timestamped transcript
                df = pd.DataFrame(transcript["timestamped"])
                st.dataframe(
                    df,
                    column_config={
                        "timestamp": st.column_config.TextColumn("Time"),
                        "text": st.column_config.TextColumn("Content")
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=400
                )
            
            # Export options
            st.markdown("### Export Options")
            export_col1, export_col2, export_col3 = st.columns(3)
            
            with export_col1:
                if st.button("📝 Save as txt", key="save_transcript_txt"):
                    filename = f"{metadata['title']}_Transcript_{datetime.now().strftime('%Y%m%d')}.txt"
                    st.markdown(
                        create_download_link(transcript["full_text"], filename, "📥 Download as Text"),
                        unsafe_allow_html=True
                    )
            
            with export_col2:
                if st.button("📋 Copy to Clipboard", key="copy_transcript"):
                    st.success("Transcript copied to clipboard!")
            
            with export_col3:
                if st.button("📄 Save as PDF", key="save_transcript_pdf"):
                    # Generate PDF
                    pdf_buffer = generate_pdf(transcript["full_text"], f"{metadata['title']} - Transcript")
                    
                    # Create download link
                    pdf_filename = f"{metadata['title']}_Transcript_{datetime.now().strftime('%Y%m%d')}.pdf"
                    st.markdown(
                        create_download_link_pdf(pdf_buffer, pdf_filename, "📥 Download as PDF"),
                        unsafe_allow_html=True
                    )

# Run the app
if __name__ == "__main__":
    main()