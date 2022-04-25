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

    var url = 'http://localhost:5000/add_link/' + yt_query;
    fetch(url)
    .then(function (response) {
      return response.json();
    }).then(function (text) {
      console.log("ADD_LINK");
      console.log(text)
    });
    
    // var url2 = 'http://localhost:5000/add_song_queue/' + yt_query;
    // fetch(url2)
    // .then(function (response) {
    //   return response.json();
    // }).then(function (text) {
    //   console.log("ADD_SONG_QUEUE");
    //   console.log(text)
    // });
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