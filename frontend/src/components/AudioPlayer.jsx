// components/AudioPlayer.js
import React, { useEffect, useRef, useState } from 'react';
import AudioIndicator from './AudioIndicator';

const AudioPlayer = ({ audioUrl, autoPlay = true }) => {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Play audio when URL changes
  useEffect(() => {
    if (audioUrl && audioRef.current && autoPlay) {
      // Reset the audio element
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      
      // Set new src and play
      audioRef.current.src = audioUrl;
      
      // Play with error handling
      const playPromise = audioRef.current.play();
      
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            // Audio playback started successfully
            setIsPlaying(true);
          })
          .catch(error => {
            console.warn("Audio playback failed:", error);
            setIsPlaying(false);
            // Many browsers require user interaction before autoplay
            // We don't need to show an error to the user for this common case
          });
      }
    }
  }, [audioUrl, autoPlay]);
  
  // Add event listeners for audio state changes
  useEffect(() => {
    const audio = audioRef.current;
    
    if (!audio) return;
    
    const handleEnded = () => setIsPlaying(false);
    const handlePause = () => setIsPlaying(false);
    const handlePlay = () => setIsPlaying(true);
    
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('play', handlePlay);
    
    return () => {
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('play', handlePlay);
    };
  }, []);

  return (
    <>
      <audio 
        ref={audioRef}
        className="hidden-audio-player" // No visible controls by default
        src={audioUrl || ''}
      />
      <AudioIndicator isPlaying={isPlaying} />
    </>
  );
};

export default AudioPlayer;