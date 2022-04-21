import React, { useEffect } from "react";
import Search from "../modules/Search.js";
import Queue from "../modules/Queue.js";

const HomePage = () => {
  return (
    <>
      <Search />
      <Queue />
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
