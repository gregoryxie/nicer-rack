import React from "react";
import { useState, useEffect } from "react";

import Song from "./Song.js"

import "../../utilities.css";
import "./Queue.css";

const Queue = () => {
  const [items, setItems] = useState([{}]);

  useEffect(() => {
    let mounted = true;
    var url = 'http://localhost:5000/get_queue/';
    fetch(url)
    .then(function (response) {
      return response.json();
    }).then(function (list) {
      if (mounted) {
        setItems(list);
      }
      return () => mounted = false;
    });
  }, []);

  console.log(items);

  return (
    <div className="Queue-container">
      <div className="Queue-title">Queue</div>
      {items.length > 0 && (
        <ul>
          {items.map(item => (
            <Song title={item.title} link={item.link} thumbnailURL={item.thumbnail} queue_index={item.index} display={false}/>
          ))}
        </ul>
      )}
    </div>
  )
}

export default Queue;