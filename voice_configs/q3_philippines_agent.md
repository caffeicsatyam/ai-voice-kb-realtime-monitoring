# Philippines Voice Bot Configuration

## Sector
Bancassurance / Life Insurance Renewal Reminder

## Languages Supported
- English (formal)
- Filipino / Tagalog
- Taglish (natural English-Filipino mix)

## ASR Configuration
- **Provider**: Browser Web Speech API
- **Language Code**: `fil-PH` (Filipino) with fallback to `en-US`
- **Known Limitations**: Web Speech API has limited Filipino/Tagalog support. May produce English transcriptions for Taglish input. Standalone Whisper with multilingual model would improve accuracy.

## TTS Configuration
- **Provider**: Browser SpeechSynthesis
- **Language**: `en-PH` (Philippine English accent)
- **Known Limitations**: No native Filipino/Tagalog voice in most browsers. Philippine English voice serves as an acceptable compromise. Edge TTS offers `fil-PH` voices as a production upgrade.

## Localization Examples

### Example 1: Greeting Adaptation
**Literal translation**: "How are you doing today, Mrs. Santos?"
**Natural Filipino**: "Kumusta po kayo, Mrs. Santos? Sana maayos po ang araw niyo."
**Why**: Filipinos naturally add a well-wishing phrase. Direct translation sounds robotic.

### Example 2: Payment Reminder
**Literal translation**: "Your payment is overdue."
**Natural Taglish**: "Ma'am, lampas na po sa due date ang payment niyo. Pero may grace period pa po tayo hanggang [date]."
**Why**: Immediately mentioning grace period is culturally expected — avoids confrontational tone.

### Example 3: Escalation
**Literal translation**: "Let me transfer you to another department."
**Natural Filipino**: "Sige po, iko-connect ko po kayo sa aming branch officer na mas makakatulong sa inyo. Sandali lang po."
**Why**: Emphasizes that the specialist will be MORE helpful (not that the current agent can't help), preserving face.

### Example 4: Objection Handling (Too Expensive)
**Literal translation**: "The premium cost is justified because..."
**Natural Taglish**: "Naiintindihan ko po, Ma'am. Medyo malaki nga po talaga ang premium. Pero kung titingnan natin, ang coverage niyo po ay [amount] — para sa pamilya niyo po 'yan, para protected po sila."
**Why**: Acknowledges the concern first ("medyo malaki nga"), then redirects to family benefit — a strong Filipino cultural motivator.

## Code-Switching Quality Notes
- Agent naturally mixes English finance terms (premium, policy, rider) with Filipino conversational phrases
- Honorific "po/opo" system is maintained throughout
- Agent does not suddenly switch to full English during escalation
- Taglish register matches informal but respectful business conversation

## Accent Coverage
- Standard Metro Manila Filipino accent
- ASR may struggle with regional accents (Visayan, Bicolano)
- TTS produces Philippine English, not native Tagalog speech

## Compliance Notes
- Never disclose full policy details before identity verification
- Always mention grace period before discussing lapse consequences
- No pressure tactics — present information and let customer decide
