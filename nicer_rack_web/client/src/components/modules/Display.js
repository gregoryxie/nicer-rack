import React from "react";
import { useState, useEffect } from "react";

import Song from "./Song.js"

import "../../utilities.css";
import "./Display.css";

const Display = (props) => {
  const [items, setItems] = useState([{}]);

  useEffect(() => {
    let mounted = true;
    var url = 'http://nicerack.mit.edu:5000/all_song_info/';
    fetch(url)
    .then(function (response) {
      return response.json();
    }).then(function (list) {
      if (mounted) {
        setItems(list.data);
        props.alterLoaded(list.data.length);
      }
      return () => mounted = false;
    });
  }, [props.loaded]);

  console.log(items);

  return (
    <div className="Display-container">
      <div className="Display-title">Downloaded Songs</div>
      {items.length > 0 && (
        <ul>
          {items.map(item => (
            <Song title={item.title} link={item.link} thumbnailURL={item.thumbnail} 
            queue_index={item.index} display={true} songs={props.songs} alterSongs={props.alterSongs}/>
          ))}
        </ul>
      )}
    </div>
  )
}

export default Display;
