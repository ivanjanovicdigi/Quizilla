// First-visit introduction of the coding assignment page (AssignmentTour.svelte).
// Each step points at one part of the page ('intro' = no part, just the welcome).
// "Seen" is remembered per browser; the tour can always be reopened with "How it works".
import { load, save } from '../storage';

export const TOUR_STEPS = ['intro', 'brief', 'code', 'guide', 'tests'] as const;
export type TourStep = (typeof TOUR_STEPS)[number];

const KEY = 'quizilla.assign.tour';

export const tourSeen = () => load<boolean>(KEY, false);
export const markTourSeen = () => save(KEY, true);
