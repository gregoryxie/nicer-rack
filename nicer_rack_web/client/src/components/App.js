import React from "react";
import { Router } from "@reach/router";
import Search from "./modules/Search.js";
import Title from "./modules/Title.js";

// To use styles, import the necessary CSS files

 const App = () => {
  return (
    <>
      <div>
        <Title />
        <Router>
          <Search default />
        </Router>
      </div>
    </>
  );
};

export default App;