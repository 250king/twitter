# X / Twitter + Piko automated builds

Automatically watches APKMirror for new X/Twitter releases, patches them with [Piko](https://github.com/crimera/piko) using [Morphe](https://github.com/MorpheApp/morphe-desktop), and publishes architecture-specific APKs plus a universal APK.

> Unofficial build automation. X/Twitter, Piko and Morphe are separate upstream projects.

## Outputs

Each release contains:

- `x-piko-<version>-arm64-v8a.apk`
- `x-piko-<version>-armeabi-v7a.apk`
- `x-piko-<version>-x86.apk`
- `x-piko-<version>-x86_64.apk`
- `x-piko-<version>-universal.apk`

The workflow runs on a schedule and can also be triggered manually with an optional X version.
