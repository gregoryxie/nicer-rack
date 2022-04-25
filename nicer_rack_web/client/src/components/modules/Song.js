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
          <p>{props.title}</p>
          <p>{props.thumbnailURL}</p>
        </div>
    </div>
  );
};

export default Song;
