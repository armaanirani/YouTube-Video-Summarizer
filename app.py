import streamlit as st
from dotenv import load_dotenv
import os
import re
import requests
from PIL import Image
from io import BytesIO
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import pandas as pd
import base64
from datetime import datetime

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
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/0.jpg"
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
            "thumbnail": video_data['snippet']['thumbnails']['high']['url']
        }
    except Exception as e:
        st.error(f"Error fetching metadata: {str(e)}")
        return {
            "title": "Unknown",
            "channel": "Unknown",
            "duration": "Unknown",
            "views": "Unknown",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/0.jpg"
        }

def extract_transcript(video_id):
    """Extract transcript from YouTube video"""
    try:
        # Get transcript directly - simpler and more reliable approach
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

def create_download_link(content, filename, link_text):
    """Create a download link for text content"""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

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
    if not youtube_url:
        st.info("Paste a YouTube URL above to get started. The app will extract the transcript and generate summaries.")
        st.markdown("#### Features:")
        st.markdown("- Extract video transcripts")
        st.markdown("- Generate concise or detailed summaries")
        st.markdown("- Create structured study notes")
        st.markdown("- Export content in various formats")
        return
    
    # Process the URL
    if youtube_url:
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
        
        # Extract transcript
        with st.spinner("Extracting transcript..."):
            transcript = extract_transcript(video_id)
            transcript = preprocess_transcript(transcript)
        
        if "error" in transcript:
            st.error(f"❌ {transcript['error']}")
            return
        
        # Summary tab
        with tab1:
            summary_type = st.radio(
                "Summary Type:",
                ["Concise", "Detailed", "Chapter-Based"],
                horizontal=True,
                key="summary_type"
            )
            
            if process_button or st.button("Generate Summary", key="gen_summary"):
                with st.spinner("Generating summary..."):
                    summary = generate_summary(transcript, summary_type.lower())
                
                st.markdown("### Summary")
                st.markdown(summary)
                
                # Export options
                st.markdown("### Export Options")
                export_col1, export_col2, export_col3 = st.columns(3)
                
                with export_col1:
                    filename = f"{metadata['title']}_Summary_{datetime.now().strftime('%Y%m%d')}.txt"
                    st.markdown(
                        create_download_link(summary, filename, "📥 Download as Text"),
                        unsafe_allow_html=True
                    )
                
                with export_col2:
                    st.button("📋 Copy to Clipboard", key="copy_summary")
                
                with export_col3:
                    st.button("📄 Save as PDF", key="save_summary_pdf", disabled=True)
        
        # Study Notes tab
        with tab2:
            if process_button or st.button("Generate Study Notes", key="gen_notes"):
                with st.spinner("Generating study notes..."):
                    notes = generate_summary(transcript, "notes")
                
                st.markdown("### Study Notes")
                st.markdown(notes)
                
                # Export options
                st.markdown("### Export Options")
                export_col1, export_col2, export_col3 = st.columns(3)
                
                with export_col1:
                    filename = f"{metadata['title']}_Notes_{datetime.now().strftime('%Y%m%d')}.txt"
                    st.markdown(
                        create_download_link(notes, filename, "📥 Download as Text"),
                        unsafe_allow_html=True
                    )
                
                with export_col2:
                    st.button("📋 Copy to Clipboard", key="copy_notes")
                
                with export_col3:
                    st.button("📄 Save as PDF", key="save_notes_pdf", disabled=True)
        
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
                filename = f"{metadata['title']}_Transcript_{datetime.now().strftime('%Y%m%d')}.txt"
                st.markdown(
                    create_download_link(transcript["full_text"], filename, "📥 Download as Text"),
                    unsafe_allow_html=True
                )
            
            with export_col2:
                st.button("📋 Copy to Clipboard", key="copy_transcript")
            
            with export_col3:
                st.button("📄 Save as PDF", key="save_transcript_pdf", disabled=True)

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
def generate_chapter_summary(transcript, video_id):
    """Generate chapter-based summary with timestamps"""
    if "error" in transcript:
        return transcript["error"]
    
    # Try to get chapters from YouTube API
    api_key = os.getenv("YOUTUBE_API_KEY")
    chapters = []
    
    if api_key:
        try:
            response = requests.get(f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={api_key}&part=snippet")
            data = response.json()
            
            if data.get('items'):
                description = data['items'][0]['snippet'].get('description', '')
                
                # Look for chapter patterns in description
                # Common format: 00:00 Chapter Title
                chapter_pattern = r'(\d{1,2}:\d{2})\s+(.*)'
                matches = re.findall(chapter_pattern, description)
                
                if matches:
                    for timestamp, title in matches:
                        chapters.append({
                            "timestamp": timestamp,
                            "title": title.strip()
                        })
        except Exception as e:
            pass
    
    # If no chapters found, use AI to generate them
    if not chapters:
        model = genai.GenerativeModel("gemini-1.5-pro")
        prompt = f"""Analyze this YouTube video transcript and create logical chapters with timestamps. 
Identify 5-8 main topics or sections in the video and provide a brief title for each.
Format your response as JSON with timestamps and titles. Example:
[
  {{"timestamp": "00:00", "title": "Introduction"}},
  {{"timestamp": "05:30", "title": "Main Topic 1"}},
  {{"timestamp": "12:45", "title": "Main Topic 2"}}
]

Transcript:
{transcript["full_text"]}
"""
        try:
            response = model.generate_content(prompt)
            import json
            chapters = json.loads(response.text)
        except Exception as e:
            # If JSON parsing fails, fall back to basic summary
            return generate_summary(transcript, "chapter")
    
    # Generate summary for each chapter
    if chapters:
        model = genai.GenerativeModel("gemini-1.5-pro")
        full_summary = "# Chapter-Based Summary\n\n"
        
        for i, chapter in enumerate(chapters):
            # Get start and end timestamps
            start_time = chapter["timestamp"]
            end_time = chapters[i+1]["timestamp"] if i+1 < len(chapters) else None
            
            # Convert timestamps to seconds for filtering
            start_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(start_time.split(":"))))
            end_seconds = None
            if end_time:
                end_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(end_time.split(":"))))
            
            # Extract transcript for this chapter
            chapter_transcript = ""
            for entry in transcript["timestamped"]:
                entry_time = entry["timestamp"]
                entry_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(entry_time.split(":"))))
                
                if entry_seconds >= start_seconds and (end_seconds is None or entry_seconds < end_seconds):
                    chapter_transcript += entry["text"] + " "
            
            # Generate summary for this chapter
            prompt = f"""You are a YouTube video summarizer expert. Provide a concise summary of this chapter section in 2-3 sentences. Focus on the main points only.

Chapter: {chapter["title"]}
Transcript:
{chapter_transcript}
"""
            try:
                response = model.generate_content(prompt)
                chapter_summary = response.text
            except Exception as e:
                chapter_summary = "Summary generation failed for this chapter."
            
            # Add to full summary
            full_summary += f"## [{chapter['timestamp']}] {chapter['title']}\n\n{chapter_summary}\n\n"
        
        return full_summary
    else:
        return generate_summary(transcript, "chapter")

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

# Run the app
if __name__ == "__main__":
    main()