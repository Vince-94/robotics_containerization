## Cheatsheet

### Initialization
Enable `RCT` (Robotic Container Tool):
```sh
source rct.sh init
```
The initalization performs the following actions:
- installing docker (if not already present)
- check docker status
- enabling `rct` cli command

It is possible to get the list of all possible commands with:
```sh
rct help
```

### Configuration
Before starting to operate, you must configure the environment, through the configuration file [env.yaml](config/env.yaml). This file is divided into 2 sections:
- Configuration: Variables that can be set freely according to the user requirements; some have placeholders and must be filled by the user.
- Constants: Variables used for abstraction, that shouldn't be modified; modification of them usually imply a modification of the logic to reflect the changes accordingly.

Furthermore, it is possible to customize dockerfiles in order to install dependencies directly in the images before building. To do that, go into the dockerfile of reference in the `docker` folder, and add the dependencies in the block highlited just below the line `TODO: Insert dependencies within this block`. Take into account also the stage (develop or deploy) of reference.

### Building
Build the dockerimage:
```sh
rct build <TARGET>
```

It will generate a docker image with the following signature: `<AUTHOR_NAME>/<WS_NAME>-<ROS2_DISTRO>-image:<TAG>`

### Running
Create/Join the container:
```sh
rct run <TARGET>
```
This will create a container with the following signature: `<AUTHOR_NAME>-<TAG>-container`

> [!NOTE]
> Executing in another terminal the same command, will end up into joining the same container (docker exec).

### Push to GitHub register
It is possible to push to GitHub register, the created docker image:
```sh
rct push <TARGET>
```

### Check configuration
Show actual environment setup:
```sh
rct config
```

### Introspection
Introspect docker images/containers:
```sh
rct status
```

### Clen up
To clean up residual images/containers:
```sh
rct clean
```

