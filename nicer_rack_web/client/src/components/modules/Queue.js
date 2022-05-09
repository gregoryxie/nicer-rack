import React from "react";
import { useState, useEffect } from "react";

import Song from "./Song.js"

import "../../utilities.css";
import "./Queue.css";

const Queue = (props) => {
  const [items, setItems] = useState([{}]);

  function getQueue() {
    var url = 'http://nicerack.mit.edu/get_queue/';
    fetch(url)
    .then(function (response) {
      return response.json();
    }).then(function (list) {
      setItems(list);
      props.alterSongs(list.length);
    }); 
  }

  useEffect(() => {
    getQueue();
    const interval = setInterval(() => {
      getQueue();
    }, 5000);
    return () => clearInterval(interval);
  }, [props.songs]);

  
  console.log(items);

  return (
    <div className="Queue-container">
      <div className="Queue-title">Queue</div>
      {items.length > 0 && (
        <ul>
          {items.map(item => (
            <Song title={item.title} link={item.link} thumbnailURL={item.thumbnail} 
            queue_index={item.index} display={false} songs={props.songs} alterSongs={props.alterSongs}/>
          ))}
        </ul>
      )}
    </div>
  )
}

export default Queue;