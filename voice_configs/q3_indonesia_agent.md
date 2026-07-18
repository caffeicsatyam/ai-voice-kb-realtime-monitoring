# Indonesia Voice Bot Configuration

## Sector
Consumer Finance / Multifinance — Installment Payment Reminders

## Languages Supported
- Formal Bahasa Indonesia (standard)
- Colloquial Bahasa Indonesia (informal Jakarta style)
- English finance loanwords (DP, tenor, top up)
- Regional accent awareness (Javanese, Sundanese, Balinese)

## ASR Configuration
- **Provider**: Browser Web Speech API
- **Language Code**: `id-ID` (Indonesian)
- **Known Limitations**: Web Speech API handles standard Bahasa Indonesia well but struggles with regional accents, especially Javanese and Sundanese. Whisper multilingual model offers better regional accent coverage.

## TTS Configuration
- **Provider**: Browser SpeechSynthesis
- **Language**: `id-ID` (Indonesian)
- **Known Limitations**: Indonesian TTS voice quality varies by browser. Chrome's Indonesian voice is acceptable. Edge TTS offers better `id-ID` voices. No regional accent TTS available — all output is standard Jakarta Indonesian.

## Localization Examples

### Example 1: Softening Penalties
**Literal translation**: "You have a late payment penalty of Rp 50,000."
**Natural Indonesian**: "Pak/Bu, karena pembayaran belum masuk sebelum jatuh tempo, ada denda Rp 50.000. Tapi kalau Bapak/Ibu melakukan pembayaran hari ini, kita bisa bantu proses segera."
**Why**: Immediately offers a solution after stating the penalty — solution-oriented approach expected in Indonesian customer service.

### Example 2: Acknowledging Regional Customers
**Context**: Customer uses Javanese expression "mboten saged" (cannot/unable).
**Response**: "Saya mengerti, Bapak. Kalau memang belum bisa bayar penuh bulan ini, kita lihat opsi lain ya. Ada pilihan bayar sebagian atau reschedule jatuh tempo."
**Why**: Responds in standard Bahasa but with extra warmth. Doesn't attempt Javanese (which would be inappropriate for a non-Javanese agent). Offers concrete alternatives.

### Example 3: Colloquial Register Shift
**Formal**: "Apakah Bapak bersedia untuk melakukan pembayaran pada hari ini?"
**Colloquial**: "Gimana, Pak? Bisa bayar hari ini nggak? Biar nggak kena denda lagi."
**Why**: Matches the customer's register. If they speak informally, rigid formal language creates distance and feels condescending.

### Example 4: English Loanword Integration
**Unnatural**: "Pembayaran pertama atau uang muka sebesar..."
**Natural**: "DP-nya sebesar Rp 5 juta, terus cicilannya per bulan Rp 1.2 juta untuk tenor 24 bulan."
**Why**: Indonesian finance conversations naturally use DP, tenor, and cicilan. Over-translating these to pure Indonesian sounds unnatural and confusing.

## Regional Accent Notes

### Javanese Accent
- **Population**: ~40% of Indonesia
- **Characteristics**: Softer consonants, "e" often pronounced as "é", tendency to add "-e" suffix
- **ASR Impact**: Moderate error rate increase. Words like "bisa" may be heard as "biso"
- **Mitigation**: If transcription quality drops, ask customer to repeat more slowly. Never mock or comment on accent.

### Sundanese Accent
- **Population**: ~15% of Indonesia
- **Characteristics**: Rising intonation at sentence ends, distinct vowel patterns
- **ASR Impact**: Generally acceptable with standard Indonesian ASR
- **Cultural Note**: May use "teh/kang" informally instead of "Ibu/Bapak"

### Balinese Accent
- **Population**: ~2% of Indonesia
- **Characteristics**: Distinct "a" pronunciation, may code-switch to Balinese
- **ASR Impact**: Higher error rate for code-switched segments

## Compliance Notes
- Never threaten legal action on reminder calls — only authorized collections
- If customer mentions financial hardship, document it and offer restructuring information
- All payment promises must be documented with date and amount
- Three consecutive missed payments trigger supervisor escalation, not increased pressure
