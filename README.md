# X / Twitter + Piko automated builds

Automatically watches APKMirror for new X/Twitter releases, patches them with [Piko](https://github.com/crimera/piko) using [Morphe](https://github.com/MorpheApp/morphe-desktop), signs them with a custom Android signing key, and publishes architecture-specific APKs plus universal APKs.

> Unofficial build automation. X/Twitter, Piko and Morphe are separate upstream projects.

## Build variants

Every X version is built in four UI / branding combinations:

| Variant | Branding | Dynamic color |
| --- | --- | --- |
| `twitter-material` | Twitter | Material You |
| `twitter` | Twitter | Standard |
| `x-material` | X | Material You |
| `x` | X | Standard |

This mirrors the old Piko build combinations. `Bring back twitter` controls Twitter vs X branding, while `Dynamic color` controls Material You colors.

Each of those four variants is built for:

- `arm64-v8a`
- `armeabi-v7a`
- `x86`
- `x86_64`
- `universal`

That produces 20 APKs per release.

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

The workflow checks APKMirror every six hours and can also be triggered manually. Manual runs can specify an X version and can force-rebuild an existing release.
