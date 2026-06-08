import type { BBox } from "../types/analysis";

export function normalizedBBoxToPixel(
  bbox: BBox,
  imageWidth: number,
  imageHeight: number,
) {
  return {
    left: bbox.x1 * imageWidth,
    top: bbox.y1 * imageHeight,
    width: (bbox.x2 - bbox.x1) * imageWidth,
    height: (bbox.y2 - bbox.y1) * imageHeight,
  };
}

export function isValidBBox(bbox?: BBox | null): bbox is BBox {
  if (!bbox) return false;
  return (
    bbox.x1 >= 0 &&
    bbox.y1 >= 0 &&
    bbox.x2 <= 1 &&
    bbox.y2 <= 1 &&
    bbox.x2 > bbox.x1 &&
    bbox.y2 > bbox.y1
  );
}

