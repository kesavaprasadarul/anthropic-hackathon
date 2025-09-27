// API endpoint to generate ElevenLabs signed URL
// This would typically be implemented as a serverless function

export async function getElevenLabsSignedUrl(agentId: string): Promise<string> {
  // Generate signed URLs using the ElevenLabs API
  const apiKey = import.meta.env.VITE_ELEVENLABS_API_KEY || process.env.ELEVENLABS_API_KEY
  
  if (!apiKey) {
    throw new Error('ElevenLabs API key not configured')
  }
  
  const response = await fetch(
    `https://api.elevenlabs.io/v1/convai/conversation/get_signed_url?agent_id=${agentId}`,
    {
      method: 'GET',
      headers: {
        'xi-api-key': apiKey
      }
    }
  )
  
  if (!response.ok) {
    throw new Error('Failed to generate signed URL')
  }
  
  const data = await response.json()
  return data.signed_url
}