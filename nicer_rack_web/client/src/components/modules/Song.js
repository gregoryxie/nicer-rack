import React from "react";

import "./Song.css";

/**
 * Prototypes:
 *
 *@param {String} title
 *@param {String} link
 *@param {String} thumbnailURL
 *@param {Integer} queue_index
 *@param {Boolean} display
 *@param {Integer} songs
 *@param {Function} alterSongs
 *
 * @returns QueueItem given paramters
 */
const Song = (props) => {
  // called when song is clicked to add to queue
  function handleQueueAdd(event) {
    // Request API to add song to the queue
    var add_queue_url = 'http://localhost:5000/add_song_queue/' + props.link;
    fetch(add_queue_url)
    .then(function (response) {
      props.alterSongs(props.songs + 1);
      console.log("ADDED SONG TO QUEUE");
      return response.json();
    });
  }

  // called when song is clicked to remove from queue
  function handleQueueRemove(event) {
    // Request API to remove the song from the queue
    var remove_queue_url = 'http://localhost:5000/remove_song_queue/' + props.link + '/' + props.queue_index;
    fetch(remove_queue_url)
    .then(function (response) {
      props.alterSongs(props.songs - 1);
      console.log("REMOVED SONG TO QUEUE");
      return response.json();
    }).then((text) => {
      console.log(text);
    });
  }

  // called when currently playing song play button is clicked
  function handlePlay(event) {
    var play_song_url = 'http://localhost:5000/play/' + props.link;
    fetch(play_song_url)
    .then(function (response) {
      console.log("STARTED PLAYING SONG");
      return response.json();
    });
  }

  // called when currently playing song play button is clicked
  function handlePause(event) {
    var pause_song_url = 'http://localhost:5000/pause/' + props.link;
    fetch(pause_song_url)
    .then(function (response) {
      console.log("PAUSED SONG");
      return response.json();
    });
  }

  return (
    <div className="Song">
        <div className="content">
          <div className="title">
            <p>{props.title}</p> 
            <div>
              {props.display == true && (
                <button onClick={handleQueueAdd} className="Song-submit-container">
                  <p>Add to Queue!</p>
                </button>
              )}
              {props.display == false && (
                <button onClick={handleQueueRemove} className="Song-submit-container">
                  <p>Remove from Queue!</p>
                </button> 
              )}
              {props.queue_index == 0 && (
                <button onClick={handlePlay} className="Song-submit-container">
                  <p>Play</p>
                </button>
              )}
              {props.queue_index == 0 && (
                <button onClick={handlePause} className="Song-submit-container">
                  <p>Pause</p>
                </button>
              )}
            </div> 
          </div>
          <div className="img">
            <img src={props.thumbnailURL} width="150" height="150"/>
          </div>
        </div>
    </div>
  );
};

export default Song;
