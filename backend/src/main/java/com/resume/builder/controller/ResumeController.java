package com.resume.builder.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.resume.builder.model.AnalysisHistory;
import com.resume.builder.model.Resume;
import com.resume.builder.repository.AnalysisHistoryRepository;
import com.resume.builder.repository.ResumeRepository;
import com.resume.builder.service.GeminiService;
import com.resume.builder.service.ResumeParserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class ResumeController {

    @Autowired
    private ResumeRepository resumeRepository;

    @Autowired
    private AnalysisHistoryRepository historyRepository;

    @Autowired
    private ResumeParserService parserService;

    @Autowired
    private GeminiService geminiService;

    @Autowired
    private ObjectMapper objectMapper;

    /**
     * Upload and parse a resume file
     */
    @PostMapping("/resumes/upload")
    public ResponseEntity<?> uploadResume(@RequestParam("file") MultipartFile file) {
        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("message", "File is empty"));
        }

        try {
            String filename = file.getOriginalFilename();
            String fileType = file.getContentType();
            String rawText = parserService.parseResume(file.getBytes(), filename);

            Resume resume = Resume.builder()
                    .filename(filename)
                    .fileType(fileType)
                    .rawText(rawText)
                    .build();

            Resume saved = resumeRepository.save(resume);

            return ResponseEntity.ok(Map.of(
                    "id", saved.getId(),
                    "filename", saved.getFilename(),
                    "fileType", saved.getFileType(),
                    "rawText", saved.getRawText()
            ));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("message", e.getMessage()));
        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", "Failed to parse file: " + e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", "An unexpected error occurred: " + e.getMessage()));
        }
    }

    /**
     * Get all resumes
     */
    @GetMapping("/resumes")
    public ResponseEntity<List<Resume>> getAllResumes() {
        return ResponseEntity.ok(resumeRepository.findAll());
    }

    /**
     * Get a single resume
     */
    @GetMapping("/resumes/{id}")
    public ResponseEntity<?> getResumeById(@PathVariable Long id) {
        return resumeRepository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * ATS Analysis and scoring
     */
    @PostMapping("/resumes/{id}/ats")
    public ResponseEntity<?> analyzeAts(@PathVariable Long id) {
        return resumeRepository.findById(id).map(resume -> {
            try {
                String result = geminiService.analyzeAts(resume.getRawText());
                JsonNode parsedResult = objectMapper.readTree(result);

                // Extract score if possible
                int score = 0;
                if (parsedResult.has("score")) {
                    score = parsedResult.get("score").asInt();
                }

                AnalysisHistory history = AnalysisHistory.builder()
                        .resumeId(resume.getId())
                        .resumeName(resume.getFilename())
                        .type("ATS_CHECK")
                        .score(score)
                        .inputData(null)
                        .resultData(result)
                        .build();

                historyRepository.save(history);

                return ResponseEntity.ok(parsedResult);
            } catch (Exception e) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                        .body(Map.of("message", "Gemini ATS analysis failed: " + e.getMessage()));
            }
        }).orElse(ResponseEntity.notFound().build());
    }

    /**
     * Job Description Alignment Matcher
     */
    @PostMapping("/resumes/{id}/match")
    public ResponseEntity<?> matchJd(@PathVariable Long id, @RequestBody Map<String, String> request) {
        String jdText = request.get("jdText");
        if (jdText == null || jdText.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("message", "Job Description text (jdText) is required."));
        }

        return resumeRepository.findById(id).map(resume -> {
            try {
                String result = geminiService.matchJobDescription(resume.getRawText(), jdText);
                JsonNode parsedResult = objectMapper.readTree(result);

                int matchPercentage = 0;
                if (parsedResult.has("match_percentage")) {
                    matchPercentage = parsedResult.get("match_percentage").asInt();
                }

                AnalysisHistory history = AnalysisHistory.builder()
                        .resumeId(resume.getId())
                        .resumeName(resume.getFilename())
                        .type("JD_MATCH")
                        .score(matchPercentage)
                        .inputData(jdText)
                        .resultData(result)
                        .build();

                historyRepository.save(history);

                return ResponseEntity.ok(parsedResult);
            } catch (Exception e) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                        .body(Map.of("message", "Gemini JD matching failed: " + e.getMessage()));
            }
        }).orElse(ResponseEntity.notFound().build());
    }

    /**
     * Cover Letter Generator
     */
    @PostMapping("/resumes/{id}/cover-letter")
    public ResponseEntity<?> generateCoverLetter(@PathVariable Long id, @RequestBody Map<String, String> request) {
        String jdText = request.get("jdText");
        if (jdText == null || jdText.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("message", "Job Description text (jdText) is required."));
        }

        return resumeRepository.findById(id).map(resume -> {
            try {
                String result = geminiService.generateCoverLetter(resume.getRawText(), jdText);
                JsonNode parsedResult = objectMapper.readTree(result);

                AnalysisHistory history = AnalysisHistory.builder()
                        .resumeId(resume.getId())
                        .resumeName(resume.getFilename())
                        .type("COVER_LETTER")
                        .score(null)
                        .inputData(jdText)
                        .resultData(result)
                        .build();

                historyRepository.save(history);

                return ResponseEntity.ok(parsedResult);
            } catch (Exception e) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                        .body(Map.of("message", "Gemini cover letter generation failed: " + e.getMessage()));
            }
        }).orElse(ResponseEntity.notFound().build());
    }

    /**
     * Interview Preparation Generator
     */
    @PostMapping("/resumes/{id}/interview-prep")
    public ResponseEntity<?> generateInterviewPrep(@PathVariable Long id) {
        return resumeRepository.findById(id).map(resume -> {
            try {
                String result = geminiService.generateInterviewPrep(resume.getRawText());
                JsonNode parsedResult = objectMapper.readTree(result);

                AnalysisHistory history = AnalysisHistory.builder()
                        .resumeId(resume.getId())
                        .resumeName(resume.getFilename())
                        .type("INTERVIEW_PREP")
                        .score(null)
                        .inputData(null)
                        .resultData(result)
                        .build();

                historyRepository.save(history);

                return ResponseEntity.ok(parsedResult);
            } catch (Exception e) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                        .body(Map.of("message", "Gemini interview prep generation failed: " + e.getMessage()));
            }
        }).orElse(ResponseEntity.notFound().build());
    }

    /**
     * Resume Rewriting Suggestions
     */
    @PostMapping("/resumes/{id}/rewrite")
    public ResponseEntity<?> generateRewrites(@PathVariable Long id) {
        return resumeRepository.findById(id).map(resume -> {
            try {
                String result = geminiService.generateRewrites(resume.getRawText());
                JsonNode parsedResult = objectMapper.readTree(result);

                AnalysisHistory history = AnalysisHistory.builder()
                        .resumeId(resume.getId())
                        .resumeName(resume.getFilename())
                        .type("REWRITE")
                        .score(null)
                        .inputData(null)
                        .resultData(result)
                        .build();

                historyRepository.save(history);

                return ResponseEntity.ok(parsedResult);
            } catch (Exception e) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                        .body(Map.of("message", "Gemini resume rewrite failed: " + e.getMessage()));
            }
        }).orElse(ResponseEntity.notFound().build());
    }

    /**
     * Get history dashboard records
     */
    @GetMapping("/history")
    public ResponseEntity<List<AnalysisHistory>> getHistory() {
        return ResponseEntity.ok(historyRepository.findAllByOrderByCreatedAtDesc());
    }

    /**
     * Get a specific history record
     */
    @GetMapping("/history/{id}")
    public ResponseEntity<?> getHistoryById(@PathVariable Long id) {
        return historyRepository.findById(id).map(history -> {
            try {
                JsonNode parsedResult = objectMapper.readTree(history.getResultData());
                // Combine history metadata and parsed result details
                return ResponseEntity.ok(Map.of(
                        "id", history.getId(),
                        "resumeId", history.getResumeId(),
                        "resumeName", history.getResumeName(),
                        "type", history.getType(),
                        "score", history.getScore() != null ? history.getScore() : 0,
                        "inputData", history.getInputData() != null ? history.getInputData() : "",
                        "resultData", parsedResult,
                        "createdAt", history.getCreatedAt()
                ));
            } catch (Exception e) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                        .body(Map.of("message", "Failed to load history details: " + e.getMessage()));
            }
        }).orElse(ResponseEntity.notFound().build());
    }

    /**
     * Delete a history record
     */
    @DeleteMapping("/history/{id}")
    public ResponseEntity<?> deleteHistory(@PathVariable Long id) {
        return historyRepository.findById(id).map(history -> {
            historyRepository.delete(history);
            return ResponseEntity.ok(Map.of("message", "History record deleted successfully"));
        }).orElse(ResponseEntity.notFound().build());
    }
}
