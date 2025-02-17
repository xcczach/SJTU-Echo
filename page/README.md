# SJTU-Echo Webpage Frontend


## Environment Prerequisite

- Node.js

## Project Setup

```sh
npm install
```

### Connect to Backend

Modify `targetHost` in `src/components/ServerConfig.js` to the address of the backend server, and
`port` to the proper port.

For example, if the backend server is running on `http://localhost:8234`, then the configuration should be:

```javascript
const targetHost = "http://localhost";
const port = "9834";
```

### Compile and Hot-Reload 

For Development:

```sh
npm run dev
```

or for production:

```sh
npm run build
```
