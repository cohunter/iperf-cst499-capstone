# Module to use Cloudflare DNS-over-HTTPS

For our cross-compiled client, DNS lookups on Android were failing due to no /etc/resolv.conf

Simple fix, just make it work: Replace the default http(s) transport with one that does name resolution itself by querying Cloudflare's DoH at 1.1.1.1

## Usage:

First install the module:

    cd ./go-doh-resolve && go install go-doh-resolve

Then import it in the program where it is needed:

    import _ ./go-doh-resolve

That's it. Now DNS resolution in the default HTTP/S client works without depending on the underlying system.

This worked for our purposes, but we do not warrant that it is suitable for any particular use case.

License: CC0 or 0BSD
