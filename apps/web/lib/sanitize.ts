import DOMPurify from "isomorphic-dompurify";

/**
 * Sanitize HTML for safe rendering via dangerouslySetInnerHTML.
 * Strips scripts, event handlers, and other dangerous markup.
 */
export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty);
}
