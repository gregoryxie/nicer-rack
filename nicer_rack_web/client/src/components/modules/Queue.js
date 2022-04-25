import React from "react";
import { useState, useEffect } from "react";

import Song from "./Song.js"

import "../../utilities.css";
import "./Queue.css";

const Queue = () => {
  const [items, setItems] = useState([{}]);
  let list = [];

  useEffect(() => {
    // api call to get queue
    // length of queue = ?
    // const item1 = {'title': 'roach - always sadge', 'thumbnail_url' : 'http://fuckoff'}
    // const item2 = {'title': 'tirstn - i wuv monsters', 'thumbnail_url' : 'http://fuckoff'}
    // const item3 = {'title': 'hebo - axolol head', 'thumbnail_url' : 'http://fuckoff'}
    // setItems([item1, item2, item3]);

    var url = 'http://localhost:5000/get_queue/';
    fetch(url)
    .then(function (response) {
      return response.json();
    }).then(function (text) {
      console.log("QUEUE");
      console.log(text);
      list = text;
      console.log(list);
    });
    // then((lis) => {
    //   for (let i=0; i<text.length; i++) {
    //     list.push({'title': text[i].title, 'thumbnailURL': text[i].thumbnail})
    //   }
    //   setItems(list);
    // });

    if (list) {
      for (let i=0; i<list.length; i++) {
        list.push({'title': list[i].title, 'thumbnailURL': list[i].thumbnail})
      }
      setItems(list);
    }

    // for (let i=0; i<list.length; i++) {
    //   list.push({'title': list[i].title, 'thumbnailURL': thumbnail})
    // }
    // // console.log(list);
    // setItems(list);
  }, []);

  const createQueue = () => {
    const queue = [];
    for (let i = 0; i < list.length; i++) {
      queue.push(<Song title={list[i].title} thumbnailURL={list[i].thumbnail_url} />);
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