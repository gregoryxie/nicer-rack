import React, { useState, useEffect } from "react";
import Download from "../modules/Download.js";
import Search from "../modules/Search.js";
import Queue from "../modules/Queue.js";
import Display from "../modules/Display.js";

const HomePage = () => {
  const [songs, setSongs] = useState(0);
  const [loaded, setLoaded] = useState(0);

  return (
    <>
      <Download loaded={loaded} alterLoaded={setLoaded}/>
      <Search />
      <Queue songs={songs} alterSongs={setSongs}/>
      <Display songs={songs} alterSongs={setSongs} loaded={loaded} alterLoaded={setLoaded}/>
    </>
  );
}

export default HomePage;
