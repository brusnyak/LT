from youtube_transcript_api import YouTubeTranscriptApi
import json
import sys

def extract_transcript(video_id):
    """
    Extract transcript from a YouTube video.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Format the output
        formatted_transcript = []
        full_text = ""
        
        for entry in transcript:
            formatted_transcript.append({
                "start": entry['start'],
                "duration": entry['duration'],
                "text": entry['text']
            })
            full_text += entry['text'] + " "
            
        return {
            "video_id": video_id,
            "full_text": full_text.strip(),
            "segments": formatted_transcript
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Default to a Knox Welles video if no argument provided
    # Example: "Smart Money Concepts Liquidity"
    video_id = sys.argv[1] if len(sys.argv) > 1 else "dQw4w9WgXcQ" # Rick Roll as placeholder, need real ID
    
    # Let's use a real trading video ID if possible, or just a placeholder
    # I'll use a placeholder for now, user can provide one
    
    print(f"Extracting transcript for video: {video_id}")
    result = extract_transcript(video_id)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        # Save to file
        filename = f"backend/research/transcript_{video_id}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Transcript saved to {filename}")
        print(f"Text length: {len(result['full_text'])} characters")
