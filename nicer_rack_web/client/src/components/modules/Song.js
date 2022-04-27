import React from "react";

import "./Song.css";

/**
 * Prototypes:
 *
 *@param {String} title
 *@param {String} thumbnailURL
 *
 * @returns QueueItem given paramters
 */
const Song = (props) => {
  return (
    <div className="Song">
        <div className="content">
          <div className="title">
            <p>{props.title}</p>  
          </div>
          <div className="img">
            <img src={props.thumbnailURL} width="150" height="150"/>
          </div>
        </div>
    </div>
  );
};

export default Song;
