const API_BASE_URL = 'http://127.0.0.1:5000';

export interface AiFeedback {
  overall_assessment: string;
  areas_to_improve: string[];
  actionable_tips: string[];
  improved_sample_answer: string;
}

export interface AnalysisResponse {
  raw_transcript: string;
  metrics: {
    wpm: number;
    confidence: number;
    clarity: number;
    total_words: number;
    filler_total: number;
    filler_breakdown: Record<string, number>;
  };
  ai_feedback: AiFeedback;
}

export class ConnectionError extends Error {
  constructor(message: string, public apiUrl: string) {
    super(message);
    this.name = 'ConnectionError';
  }
}

export class APIError extends Error {
  constructor(message: string, public status: number, public apiUrl: string) {
    super(message);
    this.name = 'APIError';
  }
}

export const analyzeAudio = async (audioBlob: Blob, duration: number): Promise<AnalysisResponse> => {
  const apiUrl = `${API_BASE_URL}/analyze`;
  
  // Log the API URL being called
  console.log(`[API] Calling backend endpoint: ${apiUrl}`);

  const formData = new FormData();
  formData.append('audio', audioBlob, 'audio.wav');
  formData.append('duration', duration.toString());

  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new APIError(
        `Analysis failed: ${response.status} ${errorText}`,
        response.status,
        apiUrl
      );
    }

    return response.json();
  } catch (error) {
    // Handle network/connection errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      // Network error - backend is likely not running
      console.error(`[API] Connection failed to ${apiUrl}`);
      throw new ConnectionError(
        'Backend server is not running. Please start the backend on port 5000.',
        apiUrl
      );
    }
    
    // Re-throw API errors
    if (error instanceof APIError || error instanceof ConnectionError) {
      throw error;
    }
    
    // Handle other fetch errors
    if (error instanceof Error) {
      if (error.message.includes('Failed to fetch') || 
          error.message.includes('NetworkError') ||
          error.message.includes('Network request failed')) {
        console.error(`[API] Network error connecting to ${apiUrl}`);
        throw new ConnectionError(
          'Backend server is not running. Please start the backend on port 5000.',
          apiUrl
        );
      }
      throw error;
    }
    
    // Unknown error
    throw new Error(`Unexpected error: ${error}`);
  }
};

