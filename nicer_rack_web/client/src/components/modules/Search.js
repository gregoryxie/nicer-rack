import React from "react";
import { useState } from "react";

import Song from "./Song.js"

import "../../utilities.css";
import "./Search.css";

/**
 * Search Box.
 */
const Search = (props) => {
  const SEARCH_ENTRY_DEFAULT_TEXT = "Search...";

  const [searchBuffer, setSearchBuffer] = useState(""); // stores text during search
  const [songs, setSongs] = useState([]);

  // called whenever the user types in the search box
  function handleChange(event) {
    setSearchBuffer(event.target.value);
  }

  // called when the user hits submit
  function handleSubmit(event) {
    event.preventDefault();
    console.log(searchBuffer);

    let mounted = true;
    var add_url = 'http://localhost:5000/search_song/' + searchBuffer;

    fetch(add_url)
    .then(function (response) {
      return response.json();
    }).then(function (list) {
      if (mounted) {
        setSongs(list.data)
      }
      return () => mounted = false;
    });
  }

  return (
    <div>
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
      {songs ? (
      <div className="Song-container">
        {songs.length > 0 && (
          <ul>
            {songs.map(song => (
              <Song title={song.title} link={song.link} thumbnailURL={song.thumbnail} 
              queue_index={song.index} display={true} songs={props.songs} alterSongs={props.alterSongs}/>
            ))}
          </ul>
        )}
    </div> ) : (
      <div></div>
    )}
  </div>
  );
};

export default Search;
