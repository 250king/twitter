# X / Twitter + Piko NewX automated builds

Automatically watches the latest stable [Piko NewX](https://github.com/crimera/piko-newx) release, asks Morphe which X/Twitter version its patch bundle supports, downloads the matching APKM from APKMirror, patches it with [Morphe](https://github.com/MorpheApp/morphe-desktop), signs it with a custom Android signing key, and publishes architecture-specific APKs plus universal APKs.

> Unofficial build automation. X/Twitter, Piko NewX and Morphe are separate upstream projects.

## Build variants

Every X version is built in two branding combinations:

| Variant | Branding |
| --- | --- |
| `twitter` | Twitter name and icons restored |
| `x` | Default X branding |

`NewX: Restore Twitter branding` controls the branding. Material You, high-contrast, Dim and the default theme are **runtime settings** in the patched app (**Piko settings → Appearance → Theme**), so they are no longer separate APKs.

Each branding variant is built for:

- `arm64-v8a`
- `armeabi-v7a`
- `universal`

That produces 6 APKs per release.

X 12.38 and newer only ship ARM native libraries, so there are no `x86` / `x86_64` builds. The workflow uses the APKMirror bundle that contains both ARM ABIs and prefers the 480–640 dpi variant.

## Custom signing

The workflow makes Morphe produce unsigned APKs, then aligns and signs them with Android `apksigner` using your own keystore. This supports normal Android JKS / PKCS12 keystores and avoids tying signing to Morphe's internal keystore format.

Create these GitHub Actions repository secrets:

- `ANDROID_KEYSTORE_BASE64` — base64-encoded contents of your keystore file
- `ANDROID_KEYSTORE_PASSWORD` — keystore password
- `ANDROID_KEY_ALIAS` — key alias
- `ANDROID_KEY_PASSWORD` — password for the key entry

On Windows PowerShell, copy the keystore as base64 with:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("D:\path\to\signing.jks")) | Set-Clipboard
```

Then open the repository's **Settings → Secrets and variables → Actions → New repository secret** and paste the value into `ANDROID_KEYSTORE_BASE64`. Add the other three secrets normally.

The workflow intentionally fails if any signing secret is missing so it never silently publishes APKs signed with a different key.

## Automation

The workflow checks the latest stable Piko NewX release every six hours. It downloads that release's `.mpp` bundle and asks Morphe (`list-versions`) which X version the bundle actually supports, then requests that exact APKM from APKMirror.

If that X version has already been published in this repository, the workflow exits before installing the Python and Android build environments.

The source APKM is downloaded once, then all six APKs are built in parallel as a GitHub Actions matrix. The release is published only after every variant succeeds.

The workflow can also be triggered manually:

- `version` — build a specific X version supported by the latest stable Piko NewX release
- `force` — rebuild and replace an existing release, for example to pick up newer Piko NewX patches for the same X version
