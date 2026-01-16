/**
 * App Context
 *
 * Reads application context from HTML meta tags.
 */

function getMeta(name: string): string {
  if (typeof document === 'undefined') return ''
  const meta = document.querySelector(`meta[name="${name}"]`)
  const content = meta?.getAttribute('content')
  return content && content !== 'None' ? content : ''
}

export const appContext = {
  csrfToken: getMeta('app:csrf-token'),
  siteName: getMeta('app:site-name'),
  currentRoute: getMeta('app:current-route'),
  userName: getMeta('app:user-name'),
  userFullName: getMeta('app:user-full-name'),
  userImage: getMeta('app:user-image'),
  userInitials: getMeta('app:user-initials'),
}
