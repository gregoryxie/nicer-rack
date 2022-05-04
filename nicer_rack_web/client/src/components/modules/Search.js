import React from "react";
import { useState } from "react";

import "../../utilities.css";
import "./Search.css";

/**
 * Search Box.
 */
const Search = () => {
  const SEARCH_ENTRY_DEFAULT_TEXT = "Search";

  const [searchBuffer, setSearchBuffer] = useState(""); // stores text during search

  // called whenever the user types in the search box
  function handleChange(event) {
    setSearchBuffer(event.target.value);
  }

  // called when the user hits submit
  function handleSubmit(event) {
    event.preventDefault();
    console.log(searchBuffer);

    var yt_query = "";
    if (searchBuffer.startsWith("https://www.youtube.com") || searchBuffer.startsWith("www.youtube.com") || searchBuffer.startsWith("youtube.com")) {
      yt_query = searchBuffer.split("youtube.com/watch?v=")[1];
      yt_query = yt_query.split("&",1)[0];
    }

    // Create url variables for API requests
    var add_url = 'http://localhost:5000/download_link/' + yt_query;

    // Request API to download the link to the server
    fetch(add_url)
    .then(function (response) {
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
        placeholder={SEARCH_ENTRY_DEFAULT_TEXT}
        value={searchBuffer}
        onChange={handleChange}
      ></input>
      <button onClick={handleSubmit} className="Submit-container">
        <i class="fa fa-search"></i>
      </button>
    </div>
  );
};

export default Search;