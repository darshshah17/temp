import React, { useState, useEffect } from 'react';
import { Upload } from 'lucide-react';
import AudioRecorder from './AudioRecorder';

const AudioUpload = ({ setInputValence }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [transcription, setTranscription] = useState('');
  const [emotion, setEmotion] = useState('');
  const [label, setLabel] = useState('');
  const [spotifyRecommendations, setSpotifyRecommendations] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [serverStatus, setServerStatus] = useState('checking');

  useEffect(() => {
    checkServerStatus();
  }, []);

  const checkServerStatus = async () => {
    try {
      const response = await fetch('http://localhost:5001/health');
      if (!response.ok) throw new Error('Server response not ok');
      const data = await response.json();
      if (data.status === 'healthy') {
        setServerStatus('running');
        setError('');
      }
    } catch (err) {
      setServerStatus('not running');
      setError('Cannot connect to server. Please ensure the Flask server is running on port 5001.');
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
    setError('');
  };

  const handleRecordingComplete = (audioFile) => {
    setSelectedFile(audioFile);
    setError('');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
  
    if (!selectedFile) {
      setError('Please select an audio file or record audio!');
      return;
    }
  
    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
  
    try {
      const response = await fetch('http://localhost:5001/upload', {
        method: 'POST',
        body: formData,
      });
  
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
  
      const data = await response.json();
      if (data.error) {
        setError(data.error);
      } else {
        setTranscription(data.transcription);
        setEmotion(data.audioFinalScore);
        setLabel(data.label);
        setSpotifyRecommendations(data.spotify_recommendations || []);
        setInputValence(data.audioFinalScore);
        setError('');
      }
    } catch (err) {
      let errorMessage = 'Error uploading file or processing transcription. ';
      if (err.name === 'TypeError') {
        errorMessage += 'No response received from server. Please check if server is running on port 5001.';
      } else {
        errorMessage += err.message;
      }
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const getEmotionColor = (score) => {
    if (score <= 0.5) {
      const redToYellow = Math.floor((score / 0.5) * 255);
      return `rgba(255, ${redToYellow}, 0, 0.5)`;
    } else {
      const yellowToGreen = Math.floor(((score - 0.5) / 0.5) * 255);
      return `rgba(${255 - yellowToGreen}, 255, 0, 0.5)`;
    }
  };


  return (
    <div className="mt-4 max-w-3xl mx-auto">
      <h4 className="text-l mb-12 text-center">Upload or Record Audio. Talk to Vibe like you would write in your diary.</h4>

      {serverStatus === 'not running' && (
        <div className="bg-yellow-100 border-l-4 border-yellow-500 p-4 mb-4">
          Server is not running. Start the Flask server.
        </div>
      )}

      <form onSubmit={handleSubmit} className="">
        <div className="flex justify-between items-center">
          <div className="flex basis-1/2 gap-4">
            <label className="bg-[#a292ff] text-zinc-950 rounded-md flex items-center px-4 py-2 cursor-pointer font-semibold">
              <input 
                type="file"
                onChange={handleFileChange}
                accept=".wav,.mp3,.m4a"
                className="hidden"
              />
              <span 
                className="truncate max-w-[125px] overflow-hidden text-ellipsis"
                title={selectedFile ? selectedFile.name : 'Select File'}
              >
                {selectedFile ? selectedFile.name : 'Select File'}
              </span>
            </label>
            <div className="flex items-center">or</div>
            <AudioRecorder onRecordingComplete={handleRecordingComplete} />
          </div>
          <button
            type="submit"
            disabled={isLoading || serverStatus === 'not running'}
            className="flex justify-end gap-2 bg-[#a292ff] px-4 py-2 rounded-md text-zinc-950 font-semibold"
          >
            <Upload size={20} />
            {isLoading ? 'Processing...' : 'Upload'}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-6 p-2 bg-red-100 border-l-4 border-red-500 text-red-700">
          Error: {error}
        </div>
      )}
      {transcription && (
        <div className="mt-6 p-2 bg-[#a292ff]/20 border-l-4 border-[#a292ff]">
          <span className='italic'>{transcription.slice(19, -1)}</span>
        </div>
      )}
      {emotion && (
        <div
          className="mt-2 p-2 border-l-4"
          style={{
            backgroundColor: `${getEmotionColor(emotion)}`,
            borderColor: getEmotionColor(emotion),
          }}
        >
          <p>Score: {(parseFloat(emotion)*100).toFixed(2)}%</p>
        </div>
      )}
      {spotifyRecommendations.length > 0 && (
        <div className="mt-4 p-4 bg-purple-100 border-l-4 border-purple-500">
          <h3 className="text-lg font-bold">Spotify Recommendations:</h3>
          <ul className="list-disc pl-6">
            {spotifyRecommendations.map((track, index) => (
              <li key={index}>
                {track.name} by {track.artist}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default AudioUpload;