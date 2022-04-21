import React from "react";
import { Router } from "@reach/router";
import Title from "./modules/Title.js";
import HomePage from "./pages/HomePage.js";

// To use styles, import the necessary CSS files

 const App = () => {
  return (
    <>
      <div>
        <Title />
        <Router>
          <HomePage default />
        </Router>
      </div>
    </>
  );
};

export default App;