import React from "react";

import "./Song.css";

/**
 * Prototypes:
 *
 *@param {String} title
 *@param {String} link
 *@param {String} thumbnailURL
 *@param {Boolean} display
 *
 * @returns QueueItem given paramters
 */
const Song = (props) => {
  // called when song queue button is clicked
  function handleSubmit(event) {
    // Request API to download the link to the server
    var add_queue_url = 'http://localhost:5000/add_song_queue/' + props.link;
    fetch(add_queue_url)
    .then(function (response) {
      console.log("ADDED SONG TO QUEUE");
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
                <button onClick={handleSubmit} className="Song-submit-container">
                  <p>Add to Queue!</p>
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
