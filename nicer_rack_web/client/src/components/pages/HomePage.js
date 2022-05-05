import React, { useState, useEffect } from "react";
import Search from "../modules/Search.js";
import Queue from "../modules/Queue.js";
import Display from "../modules/Display.js";

const HomePage = () => {
  const [songs, setSongs] = useState(0);

  return (
    <>
      <Search />
      <Queue songs={songs} alterSongs={setSongs}/>
      <Display songs={songs} alterSongs={setSongs}/>
    </>
  );
}

export default HomePage;



// const Profile = (props) => {
//   useEffect(() => {
//     document.title = "Profile Page";
//   }, [props.profileId]);

//   return ( props.userId ? 
//     <>
//       <PageInfo profileId={props.profileId} userId={props.userId} />
//       <PageContent userId={props.profileId}></PageContent>
//     </>
//     : 
//     <>loading</>
//   );
// };

// export default Profile;
