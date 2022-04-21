import React from "react";
import { useState, useEffect } from "react";

import Song from "./Song.js"

import "../../utilities.css";
import "./Queue.css";

const Queue = () => {
  const [items, setItems] = useState([{}]);

  useEffect(() => {
    // api call to get queue
    // length of queue = ?
    const item1 = {'title': 'roach - always sadge', 'thumbnail_url' : 'http://fuckoff'}
    const item2 = {'title': 'tirstn - i wuv monsters', 'thumbnail_url' : 'http://fuckoff'}
    const item3 = {'title': 'hebo - axolol head', 'thumbnail_url' : 'http://fuckoff'}
    setItems([item1, item2, item3]);
  }, []);

  const createQueue = () => {
    const queue = [];
    for (let i = 0; i < items.length; i++) {
      queue.push(<Song title={items[i].title} thumbnailURL={items[i].thumbnail_url} />);
    }
    return queue;
  };

  const queue = createQueue();

  return (
    <div className="Queue-container">
      <div className="Queue-title">Queue</div>
      {queue}
    </div>
  )
}

export default Queue;