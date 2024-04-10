segment_counter = 0

# Process each segment
for i, sentence_segment in enumerate(final_list):
    # Initialize a variable to hold the adjusted start_ms for the next segment
    next_start_ms = None
    next_start_ms_adjustment = 0.0

    for index, segment in enumerate(sentence_segment):
        start_ms = seconds_to_milliseconds(segment["start"] + next_start_ms_adjustment)
        print(f"This is the original text for segment {index}: ", segment["text"])
        print(
            f"This is the original start for segment {index}: ",
            seconds_to_milliseconds(segment["start"]),
        )
        print(f"This is the adjusted start for segment {index}: ", start_ms)

        end_ms = seconds_to_milliseconds(segment["end"])

        # Adjust end_ms and plan adjustment for next segment's start_ms based on the score
        if segment["last_word_score"] < 0.35:
            # end_ms += seconds_to_milliseconds(1)
            # next_start_ms_adjustment = 0.5
            if index + 1 < len(sentence_segment):
                next_segment_start_ms = seconds_to_milliseconds(
                    sentence_segment[index + 1]["start"]
                )
                half_distance = (next_segment_start_ms - end_ms) / 2
                end_ms += half_distance
            else:
                end_ms += seconds_to_milliseconds(
                    1
                )  # Or any other logic for last segment
            next_start_ms_adjustment = 0.5  # Adjusting next start time by 0.5 seconds
            print(
                f"This is the original end for segment {index}: ",
                seconds_to_milliseconds(segment["end"]),
            )
            print(f"This is the adjusted end for segment {index}: ", end_ms)
            print("massive change for next start")
        elif segment["last_word_score"] < 0.7:
            end_ms += seconds_to_milliseconds(0.5)
            next_start_ms_adjustment = 0.2
            print(
                f"This is the original end for segment {index}: ",
                seconds_to_milliseconds(segment["end"]),
            )
            print(f"This is the adjusted end for segment {index}: ", end_ms)
            print("simple change for next start")
        else:
            next_start_ms_adjustment = 0  # No adjustment needed

        # Extract the segment from the full song
        segment_audio = song[start_ms:end_ms]

        # Save the segment to dir
        segment_filename = f"{base_directory}/segment_{segment_counter}.mp3"
        segment_audio.export(segment_filename, format="mp3")
        print(f"Segment saved as {segment_filename}")

        segment_counter += 1
