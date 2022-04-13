import React from "react";
import { useState, useEffect } from "react";

/**
 * Search Box.
 */
const Search = () => {
  const SEARCH_ENTRY_DEFAULT_TEXT = "Search";

  const [searchValue, setSearchValue] = useState(""); // the link / song to be searched
  const [searchBuffer, setSearchBuffer] = useState(""); // stores text during search

  // called whenever the user types in the search box
  function handleChange(event) {
    setSearchBuffer(event.target.value);
  }

  // called when the user hits submit
  function handleSubmit(event) {
    event.preventDefault();
    setSearchValue(searchBuffer); // set the current bio to whatever is in the bioBuffer
    console.log(searchValue);
  }

  return (
    <>
      <input
        type="text"
        placeholder={SEARCH_ENTRY_DEFAULT_TEXT}
        value={searchBuffer}
        onChange={handleChange}
      ></input>
      <button onClick={handleSubmit}>submit</button>
    </>
  );
};

export default Search;