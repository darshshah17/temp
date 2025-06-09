import React, { useEffect, useState, useCallback } from 'react';
import SpotifyAuth from './SpotifyAuth';
import AudioUpload from './components/AudioUpload';

import vibeLogo from './images/VibeLogo.png';


function App() {
  const [token, setToken] = useState('');
  const [tracks, setTracks] = useState([]);
  const [inputValence, setInputValence] = useState(0.5);
  const [numTopTracks, setNumTopTracks] = useState(5);
  const [isAudioParsed, setIsAudioParsed] = useState(false);
  const [isLoading, setIsLoading] = useState(false); // Loading state

  // Function to handle pagination for Spotify API
  const fetchPaginatedData = async (url, token, items = []) => {
    try {
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await response.json();
      items = items.concat(data.items || []);

      if (data.next) {
        return fetchPaginatedData(data.next, token, items);
      }

      return items;
    } catch (error) {
      console.error('Error fetching paginated data:', error);
      return items;
    }
  };

  const fetchAllPlaylistsAndTracks = useCallback(async () => {
    let allTracks = [];

    try {
      let playlists = await fetchPaginatedData('https://api.spotify.com/v1/me/playlists', token);
      playlists = playlists.filter(playlist => playlist.public);

      for (let playlist of playlists) {
        let tracks = await fetchPaginatedData(`https://api.spotify.com/v1/playlists/${playlist.id}/tracks`, token);

        tracks.forEach(track => {
          if (track.track) {
            allTracks.push({
              id: track.track.id,
              name: track.track.name,
              artist: track.track.artists[0].name,
              uri: track.track.uri,
            });
          }
        });
      }
      setTracks(allTracks);
    } catch (error) {
      console.error('Error fetching public playlists or tracks:', error);
    }
  }, [token]);

  useEffect(() => {
    const hash = window.location.hash;
    let storedToken = window.localStorage.getItem('spotify_token');
    const expirationTime = window.localStorage.getItem('spotify_token_expiry');

    if (storedToken && expirationTime && new Date().getTime() < expirationTime) {
      setToken(storedToken);
    } else {
      window.localStorage.removeItem('spotify_token');
      window.localStorage.removeItem('spotify_token_expiry');
      storedToken = null;
    }

    if (!storedToken && hash) {
      const tokenMatch = hash.substring(1).split('&').find(elem => elem.startsWith('access_token'));
      if (tokenMatch) {
        const token = tokenMatch.split('=')[1];
        const expiresIn = 3600 * 1000;
        const expirationTime = new Date().getTime() + expiresIn;

        window.location.hash = '';
        window.localStorage.setItem('spotify_token', token);
        window.localStorage.setItem('spotify_token_expiry', expirationTime);
        setToken(token);
      }
    }
  }, []);

  useEffect(() => {
    if (token) {
      fetchAllPlaylistsAndTracks();
    }
  }, [token, fetchAllPlaylistsAndTracks]);  


  const sendTracksToBackend = async () => {
    console.log("sendTracksToBackend called with tracks:", tracks); 
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:5001/analyze-tracks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ tracks, input_final_score: inputValence }),  
      });
  
      const data = await response.json();
      console.log("Data from backend:", data); 
      let updatedTracks = data.tracks || [];
      setTracks(updatedTracks);
    } catch (error) {
      console.error('Error sending tracks to backend:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  

  const handleNumTopTracksChange = (event) => {
    setNumTopTracks(parseInt(event.target.value, 10));
  };

  const handleAudioParsingSuccess = (audioFinalScore) => {
    setInputValence(audioFinalScore);  
    setIsAudioParsed(true);
  };

  const openSpotifyLink = (trackId) => (e) => {
    e.preventDefault();
    const appLink = `spotify:track:${trackId}`;
    const webLink = `https://open.spotify.com/track/${trackId}`;
    
    // Try opening the Spotify app URI
    window.location.href = appLink;

    // Fallback to the web link if app URI fails
    setTimeout(() => {
      window.open(webLink, "_blank");
    }, 500);
  };

  return (
    <div className="bg-[#a292ff]/0 max-w-3xl mx-auto my-16">
      <div className="flex gap-1 items-center justify-center">
        <h1 className="text-6xl text-center font-bold">Vibe</h1>
        <img src={vibeLogo} alt="Vibe Logo" className="w-20"/>
      </div>
      {!token ? (
        <SpotifyAuth />
      ) : (
        <>
          <AudioUpload setInputValence={handleAudioParsingSuccess} />
          
          {isAudioParsed && (
            <div className="mt-6">
              <h2 className="text-2xl">All Tracks from All Playlists</h2>

              <div className="mb-2 mt-2 flex justify-between items-center">
                <label htmlFor="numTopTracks">
                  View{' '}
                  <select id="numTopTracks" className="bg-[#a292ff]/40 rounded-md px-1 py-0.5" value={numTopTracks} onChange={handleNumTopTracksChange}>
                    <option value="5">Top 5</option>
                    <option value="10">Top 10</option>
                    <option value="20">Top 20</option>
                    <option value={tracks.length}>All</option>
                  </select>
                  {' '}Tracks That Match Your Vibe:
                </label>
                <button onClick={sendTracksToBackend} className="px-4 py-2 rounded-md bg-[#a292ff] text-zinc-950 font-semibold">Analyze Tracks</button>
              </div>

              {isLoading ? (
                <p>Loading...</p>
              ) : tracks.length > 0 ? (
                <>
                  <ul>
                    {tracks.slice(0, numTopTracks).map((track, index) => (
                      <li key={index} className="border-b border-gray-400 py-2">
                        <a 
                          href={`https://open.spotify.com/track/${track.id}`} 
                          onClick={openSpotifyLink(track.id)}
                          className="font-bold hover:underline"
                        >
                          {track.name}
                        </a> 
                        <span className="italic ml-1">by {track.artist}</span>
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <p>No tracks found.</p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default App;