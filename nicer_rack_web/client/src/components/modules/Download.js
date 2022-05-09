import React from "react";
import { useState } from "react";

import "../../utilities.css";
import "./Download.css";

/**
 * Download Box.
 */
const Download = (props) => {
  const DOWNLOAD_ENTRY_DEFAULT_TEXT = "Download...";

  const [downloadBuffer, setDownloadBuffer] = useState(""); // stores text during search

  // called whenever the user types in the search box
  function handleChange(event) {
    setDownloadBuffer(event.target.value);
  }

  // called when the user hits submit
  function handleSubmit(event) {
    event.preventDefault();
    console.log(downloadBuffer);

    var yt_query = "";
    if (downloadBuffer.startsWith("https://www.youtube.com") || downloadBuffer.startsWith("www.youtube.com") || downloadBuffer.startsWith("youtube.com")) {
      yt_query = downloadBuffer.split("youtube.com/watch?v=")[1];
      yt_query = yt_query.split("&",1)[0];
    }

    // Create url variables for API requests
    var add_url = 'http://nicerack.mit.edu/download_link/' + yt_query;

    // Request API to download the link to the server
    fetch(add_url)
    .then(function (response) {
      props.alterLoaded(props.loaded + 1);
      return response.json();
    }).then(function (text) {
      console.log("DOWNLOAD_LINK");
      console.log(text)
    });
  }

  return (
    <div className="Search-container">
      <input
        className="Search-bar-container"
        type="text"
        placeholder={DOWNLOAD_ENTRY_DEFAULT_TEXT}
        value={downloadBuffer}
        onChange={handleChange}
      ></input>
      <button onClick={handleSubmit} className="Submit-container">
        <i class="fa fa-search"></i>
      </button>
    </div>
  );
};

export default Download;