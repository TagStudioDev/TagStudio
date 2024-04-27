# [EXPERIMENTAL] Tauri version of TagStudio

<p align="center">
  <img width="60%" src="github_header.png">
</p>

> [!CAUTION]
> This is an experimental and **unfinished** version of TagStudio written in [tauri](https://tauri.app/). Do not expect this to work as of now.
> Contributions are very welcome.

This is a **_very_** cutdown version of the [Upstream Readme](https://github.com/CyanVoxel/TagStudio), only focusing on information about this specific build of TagStudio.

## Contents

- [Readme of Upstream Repo](https://github.com/CyanVoxel/TagStudio)
- [Devstack](#devstack)
- [Todo List](#todo)
- [Building](#building)

## Devstack

- [Tauri](https://tauri.app/)
- [Rust](https://www.rust-lang.org/)
- [SvelteKit](https://kit.svelte.dev/) w/ [TypeScript](https://www.typescriptlang.org/)
- [TailwindCSS](https://tailwindcss.com/)
- [DaisyUI](https://daisyui.com/)
- [Inlang's ParaglideJS](https://inlang.com/)

## TODO

Top Priority:

- [x] Have a working window
- [x] Build the app i18n ready (continous)
- [ ] Expand Building Instructions
- [ ] UI Layout and design
- [ ] Have a mostly complete frontend
- [ ] Expanding this list

Low Priority:

- [ ] Start working on backend (only after having a somewhat useable frontend)
- [ ] Translations
  - [x] English (native)
  - [ ] German
  - [ ] French
  - [ ] Spanish
  - [ ] Whatever else is needed
- [ ] Themes
  - [ ] Additional Themes
  - [ ] Easy Theme Hue Adjustion
  - [ ] Fully Custom Themes

## Building

Thanks Tauri's documentation, the OS specific installations are documented there.

### Step 1.

- Installing Tauri and Rust according to **[Tauri's documentation](https://tauri.app/v1/guides/getting-started/prerequisites)**
- We also intend to use a JavaScript frontend framework, so **we need Node.js installed** as well (also in the docs above).

### Step 2.

- Cloning the project

```
git clone https://github.com/AdamTmHun/TagStudio.git
cd TagStudio
```

### Step 3.

- Installing packages
- We recommend using [pnpm](https://pnpm.io/) as package manager. It's fast, space efficient. It's just better.

```
pnpm install
```

### Step 4.

- You can now run a dev server, or build the project.
  > [!WARNING]
  > You may need the `WEBKIT_DISABLE_COMPOSITING_MODE=1` AND/OR `WEBKIT_DISABLE_DMABUF_RENDERER=1`enviroment variable while running the command below if you get a blank screen.

```
pnpm tauri dev
```

- Building and then running the project.
  > [!CAUTION]
  > Linux: It requires `NO_STRIP=true` as enviroment variable due to a bug in linuxdeploy, which is used to build .Appimage file.

```
pnpm tauri build
```

### Step 5.

> [!WARNING]
> You may need the `WEBKIT_DISABLE_COMPOSITING_MODE=1` AND/OR `WEBKIT_DISABLE_DMABUF_RENDERER=1` enviroment variable while running the command below if you get a blank screen.

- Locate the binary in `/src-tauri/target/release/bundle`, pray and then run it.
