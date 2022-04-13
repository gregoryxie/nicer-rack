import React from "react";
import { Router } from "@reach/router";
import Search from "./modules/Search.js";

// To use styles, import the necessary CSS files

 const App = () => {
  return (
    <>
      <div>
        <Search />
        <Router>
        </Router>
      </div>
    </>
  );
};

export default App;