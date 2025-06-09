import React from 'react';

const CLIENT_ID = '336f13e12a424981935b38ffd0289426'; // Replace with your actual client ID
const REDIRECT_URI = 'http://localhost:3000';  // Update the redirect URI
const AUTH_ENDPOINT = 'https://accounts.spotify.com/authorize';
const RESPONSE_TYPE = 'token';

const SpotifyAuth = () => {
  const loginToSpotify = () => {
    // No scope specified, as only public playlists are needed
    window.location.href = `${AUTH_ENDPOINT}?client_id=${CLIENT_ID}&redirect_uri=${REDIRECT_URI}&response_type=${RESPONSE_TYPE}`;
  };

  return (
    <div className="flex flex-col items-center justify-center mr-4">
      <button 
        onClick={loginToSpotify} 
        className="px-4 py-2 rounded-md bg-[#a292ff] text-zinc-950 font-semibold mt-12"
      >
        Login to Spotify
      </button>
    </div>
  );
};

export default SpotifyAuth;
