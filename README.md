<a name="readme-top"></a>

<div align="center">
  <a href="https://github.com/Laxeros07/Question-Answering-about-Geometries">
    <img src="https://github.com/Laxeros07/Question-Answering-about-Geometries/blob/main/App/frontend/public/images/AGQA.png?raw=true" alt="Logo" width="15%" height="15%">
  </a>
<h3 align="center">AGQA</h3> 
 Ask Germany about its administrative geometries!
  <p align="center">
        <br />
   made <a href="https://tu-dresden.de/bu/umwelt/geo/geoinformatik"> @ TU - Dresden</a> 🌍
    <br />
    <a href="https://github.com/Laxeros07/Question-Answering-about-Geometries/tree/main/App"><strong>Explore the code »</strong></a>
  </p>
</div>
<p align="center">
-- ⭔ ⌕ - 𓅃 - ⌕ ⭔ --
</p>
<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#about-the-project">About The Project</a></li>
    <li><a href="#questions-answered-by-the-application">Example Questions</a></li>
    <li><a href="#built-with">Built With</a></li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#local-environment">Local environment</a></li>
        <li><a href="#docker">Docker</a></li>
      </ul>
    </li>
    <li><a href="#usage-goals">Usage goals</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

# About The Project

This project is a further development of [Chat with NRW](https://github.com/Felioxx/SIS-Course). It was done during the summer of 2026 at TU Dresden.

An interactive Web application was implemented that includes a Chat function, which is linked to a leaflet map. The Application is knowledgeable about the administrative geometries and the federal relations of Germany. 

<br />
<div class="container">
      <div class="image">
        <img align=left width="30%"  src="https://github.com/Laxeros07/Question-Answering-about-Geometries/blob/main/App/frontend/public/images/screenshot_api.png?raw=true">
      </div>
      <div class="text">
        <p align=justify><a> In order to use the chatbot, one has to enter a purchased </a> <a href="https://openai.com/index/openai-api/">Open AI API Key</a> <a>            The field for entering the  key opens on loading the /chat page.</a>
          <p>
      </div>
    </div>
<br />
<br />
<br />
<br />
<br />
<br />
<br />
<div class="container">
  <div class="image">
    <img align=left width="60%" src="https://github.com/Laxeros07/Question-Answering-about-Geometries/blob/main/App/frontend/public/images/screenshot_chat.png?raw=true">
  </div>
  <div class="text">
    <p align=justify><a>On the left side of the page is the chat where you can asks questions similar to our listet examples. After asking the question the chatbot takes some time to generate the answer. When the answer is computet, the named entities in question and answer are visualized on the right side on the leaflet map.</a>
      <p>
  </div>
</div> 
<br />
<br />
<br />
<br />
<br />
<br />
<p align="right">(<a href="#readme-top">back to top</a>)</p>

# Questions answered by the application

### Hierarchy of the entities:

City < Administrative Community < District < Administrative District < Federal State < State

### Regarding location

- Where is (_entity_name_) located?

### Regarding federal levels

- Which cities lie in the district of (_entity_name_)?
- Which cities/districts lie in the administrative district of (_entity_name_)?

### Regarding relations between entities

#### distances

- What is the distance between (_city_name_) and (_city_name_)?
- What is the distance between (_district_name_) and (_district_name_)?
- What is the distance between (_administrative_district_name_) and (_administrative_district_name_)?

#### cardinal directions

- Show me every city that lies western of (_city_name_)?
- Show me every district that lies western of (_district_name_)?
- Show me every administrative district that lies western of (_administrative_district_name_)?
- Is (_city_name_) cardinaldirection = north|west|east|south from (_city_name_)?
- Is (_district_name_) cardinaldirection = north|west|east|south from (_district_name_)?
- Is (_administrative_district_name_) cardinaldirection = north|west|east|south from (_administrative_district_name_)?

#### neighbors

- Show me all neighbors of (_entity_name_)?
<p align="right">(<a href="#readme-top">back to top</a>)</p>
<br />

## Built With

- [![JavaScript][JavaScript.com]][JavaScript-url]
- [![React][React.js]][React-url]
- [![python][python.com]][python-url]
- [![fastAPI][fastAPI-shield]][fastAPI-url]
- [![nodeJS][nodeJS.com]][nodeJS-url]
- [![Bootstrap][Bootstrap.com]][Bootstrap-url]
- [![neo4j][neo4j.com]][neo4j-url]
- [![openAi][openAi.com]][openAi-url]
- [![SAIA API][saia.com]][saia-url]
- [![StackOverflow][StackOverflow.com]][StackOverflow-url]

<p align="right">(<a href="https://github.com/Felioxx/SIS-Course?tab=readme-ov-file#chat-with-nrw">back to top</a>)</p>

<!-- GETTING STARTED -->

# Getting Started

## Local environment

### Requirements:

- Install the [Neo4j Commmunity Edition](https://neo4j.com/product/community-edition/)

### Installation:

1. Clone the repo
   ```sh
   https://github.com/Laxeros07/Question-Answering-about-Geometries
   ```
2. Install NPM packages in the frontend directory.
   ```sh
   cd App/frontend
   npm install
   ```
3. Install python requirements in the backend directory.
   ```sh
   cd App/backend
   pip install -r requirements.txt
   ```
4. Before starting the backend make sure Neo4j is running:

   4.1. Open a console and navigate to the installation directory.

   4.2. Start the server:
   - Windows, use:

   ```sh
   bin\neo4j-admin server console
   ```

   - Linux/Mac, use:

   ```sh
   ./bin/neo4j-admin server console
   ```

   For full instructions, see https://neo4j.com/docs/operations-manual/current/installation/

   4.3. open http://localhost:7474/

5. Fill the database.

- Open https://data-importer.neo4j.io/
- Click on Browse and select all files in the folder neo4j_data
- Click on the three points next to "run model". Click on "Open model" and select the JSON file in the Graph folder.
- Then run the import to fill the database

6. Start the backend

   ```bash
   cd App_new/backend
   uvicorn api.main:app --reload --port 8000
   ```

- runs on: `http://localhost:8000`

7. Start the frontend

   ```bash
   cd App_new/frontend
   npm start
   ```

- runs on: `http://localhost:3000`

## Docker

### Requirements:

- Install [Docker](https://docs.docker.com/engine/install/)

### Installation:

1. Clone the repo
   ```sh
   https://github.com/Laxeros07/Question-Answering-about-Geometries
   ```
2. Build the App

   ```sh
   cd .\App\
   docker compose up --build
   ```

- runs on: `http://localhost:3000`
<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->

# Usage goals

### Importance of the application

- Works with the “complete” geometries
- Has knowledge about the spatial relations between the administrative entities
- Visualization of the spatial context of the answers on an interactive map
- Easy to use because of its narrower scope than general-purpose applications (e.g. Google Maps, Bing Maps)

### Target users

- Local government workers
- Citizens
- Programmers of Geographic Information Systems and Map-based applications, looking for high and low resolution boundaries for the spatial entities

### Benefits for the users

- Easy usage
- Precise visualization
- Correct distances
- Explanation of the federal system

<p align="right">(<a href="https://github.com/Felioxx/SIS-Course?tab=readme-ov-file#chat-with-nrw">back to top</a>)</p>

<!-- LICENSE -->

# License

Copyright (c) 2027

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->

# Contact

Auriol Degbelo - auriol.degbelo@tu-dresden.de

Eva Langstein - elangste@uni-muenster.de

Anne Staskiewicz - anne.staskiewicz@uni-muenster.de

Felix Disselkamp - fdisselk@uni-muenster.de

<p align="right">(<a href="#readme-top">back to top</a>)</p>
<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/github_username/repo_name.svg?style=for-the-badge
[contributors-url]: https://github.com/github_username/repo_name/graphs/contributors
[fastAPI-url]: https://fastapi.tiangolo.com/
[fastAPI-shield]: https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi
[forks-shield]: https://img.shields.io/github/forks/github_username/repo_name.svg?style=for-the-badge
[forks-url]: https://github.com/github_username/repo_name/network/members
[stars-shield]: https://img.shields.io/github/stars/github_username/repo_name.svg?style=for-the-badge
[stars-url]: https://github.com/github_username/repo_name/stargazers
[issues-shield]: https://img.shields.io/github/issues/github_username/repo_name.svg?style=for-the-badge
[issues-url]: https://github.com/github_username/repo_name/issues
[license-shield]: https://img.shields.io/github/license/github_username/repo_name.svg?style=for-the-badge
[license-url]: https://github.com/github_username/repo_name/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com
[JavaScript.com]: https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E
[JavaScript-url]: https://www.javascript.com/
[saia-url]: https://saia.gwdg.de/
[saia.com]: https://img.shields.io/badge/-SAIA%20API-eee?style=for-the-badge
[StackOverflow-url]: https://stackoverflow.com/
[StackOverflow.com]: https://img.shields.io/badge/-Stackoverflow-FE7A16?style=for-the-badge&logo=stack-overflow&logoColor=white
[openAi-url]: https://openai.com/
[openAi.com]: https://img.shields.io/badge/-OpenAI%20API-eee?style=for-the-badge&logo=openai&logoColor=412991

[nodeJS-url]: [https://pixijs.com/](https://nodejs.org/en)
[nodeJS.com]: https://img.shields.io/badge/node.js-6DA55F?style=for-the-badge&logo=node.js&logoColor=white
[neo4j.com]: https://img.shields.io/badge/neo4j-4581C3?style=for-the-badge&logo=neo4j&logoColor=white
[neo4j-url]: https://neo4j.com/
[python.com]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[python-url]: https://www.python.org/
