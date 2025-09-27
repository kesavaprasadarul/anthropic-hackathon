// Simple API route to generate ElevenLabs signed URL
// In a real app, this would be a serverless function

interface SignedUrlRequest {
  agentId: string
}

interface SignedUrlResponse {
  signedUrl: string
}

export async function POST(request: Request): Promise<Response> {
  try {
    const { agentId }: SignedUrlRequest = await request.json()
    
    if (!agentId) {
      return new Response(JSON.stringify({ error: 'Agent ID is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      })
    }

    // Use your provided API key directly for now
    // In production, this should come from environment variables
    const apiKey = 'sk_12e21f2dc9aa3ad1261f9ed020ca3254c2f84a5cd90b0f30'
    
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
      throw new Error(`ElevenLabs API error: ${response.status}`)
    }
    
    const data = await response.json()
    
    return new Response(JSON.stringify({ signedUrl: data.signed_url }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })
    
  } catch (error) {
    console.error('Signed URL generation error:', error)
    return new Response(
      JSON.stringify({ error: 'Failed to generate signed URL' }), 
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    )
  }
}