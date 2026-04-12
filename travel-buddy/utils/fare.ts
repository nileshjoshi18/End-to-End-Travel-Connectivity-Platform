// utils/fare.ts
export const calculateAutoFare = (distanceInKm: number): number => {
  const minFare = 26;
  const minDistance = 1.5;
  const ratePerKm = 17.14;

  if (distanceInKm <= minDistance) {
    return minFare;
  }
  
  const additionalDistance = distanceInKm - minDistance;
  return Math.round(minFare + (additionalDistance * ratePerKm));
};