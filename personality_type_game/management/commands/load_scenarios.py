from django.core.management.base import BaseCommand
from personality_type_game.models import Scenario


class Command(BaseCommand):
    help = 'Load initial scenarios for the personality type game'

    def handle(self, *args, **options):
        self.stdout.write('Loading scenarios...')
        
        scenarios_data = [
            # DRIVER scenarios (Easy)
            {
                'difficulty': 'easy',
                'scenario_title': 'Deadline Pressure - Driver',
                'transcript': [
                    'Manager: "The client needs this by Friday. Can you make it happen?"',
                    'Employee: "Friday? That\'s in two days. What are my options here?"',
                    'Manager: "We could extend, but they\'re offering a bonus for early delivery."',
                    'Employee: "What\'s the fastest path? I need to see the timeline and deliverables now."',
                    'Manager: "Here\'s the breakdown..."',
                    'Employee: "Got it. I\'ll handle this. Just make sure no one blocks me."'
                ],
                'correct_type': 'driver',
                'tell_category': 'control',
                'tell_explanation': 'The employee asks for options, timeline, and autonomy ("no one blocks me"), showing a need for control over the situation.',
                'response_choices': {
                    'A': 'Let me check with the team first and get back to you.',
                    'B': 'Here are your options: Option 1 takes 3 days, Option 2 takes 4. The fastest path is Option 1 if I have full autonomy.',
                    'C': 'I understand this is stressful. Would you like to talk through how you\'re feeling?',
                    'D': 'This requires careful analysis. Let me gather all the data first.'
                },
                'correct_response': 'B',
                'response_explanation': 'Drivers need options, clear outcomes, and autonomy. Providing concrete options with autonomy addresses their control need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Meeting Takeover - Driver',
                'transcript': [
                    'Team Lead: "So, we have three proposals. Let\'s discuss..."',
                    'Driver: "I\'ve already reviewed them. Proposal 2 is the fastest. Can we vote now?"',
                    'Team Lead: "But we haven\'t heard everyone\'s input yet."',
                    'Driver: "Time is money. What\'s the decision point here? I need a clear answer."'
                ],
                'correct_type': 'driver',
                'tell_category': 'control',
                'tell_explanation': 'The driver wants to control the pace and decision-making, showing urgency and impatience with process.',
                'response_choices': {
                    'A': 'I appreciate your enthusiasm, but let\'s make sure everyone feels heard first.',
                    'B': 'You make a good point about speed. Let\'s set a 10-minute timer for discussion, then vote.',
                    'C': 'This must be frustrating. How are you feeling about the process?',
                    'D': 'Before we vote, let\'s review the detailed cost-benefit analysis of each proposal.'
                },
                'correct_response': 'B',
                'response_explanation': 'Giving a time-bound process with a clear decision point addresses the driver\'s need for speed and control.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Feels Unheard - Driver',
                'transcript': [
                    'Driver: "I\'ve been suggesting this approach for weeks. No one listens."',
                    'Colleague: "We hear you, but we need to consider all perspectives."',
                    'Driver: "That\'s what you always say. Meanwhile, we\'re wasting time and money."',
                    'Colleague: "Let\'s schedule a meeting to discuss..."',
                    'Driver: "More meetings? That\'s the problem. I need someone to make a decision and move forward."'
                ],
                'correct_type': 'driver',
                'tell_category': 'control',
                'tell_explanation': 'The driver feels their suggestions are being blocked by endless process, threatening their need for control and action.',
                'response_choices': {
                    'A': 'I understand you feel frustrated. Would you like to talk about how this makes you feel?',
                    'B': 'You\'re right. Let\'s make a decision today. Here are the options: Option A (your approach), Option B, or Option C. I\'ll decide by 3pm.',
                    'C': 'Thank you for your patience. We truly value your input and want to make sure everyone feels included.',
                    'D': 'Before we decide, let\'s review the data from all three approaches systematically.'
                },
                'correct_response': 'B',
                'response_explanation': 'Drivers need action, not process. Offering clear options with a decision timeline and autonomy addresses their control need.',
                'is_feels_unheard': True
            },
            
            # EXPRESSIVE scenarios
            {
                'difficulty': 'easy',
                'scenario_title': 'Team Recognition - Expressive',
                'transcript': [
                    'Manager: "Great job on the project, everyone."',
                    'Expressive: "Thank you! I was so excited about the presentation. Did you see how the client reacted?"',
                    'Manager: "Yes, they seemed pleased."',
                    'Expressive: "Exactly! I worked really hard on those visuals. I think we should share this success with the whole company!"',
                    'Manager: "Maybe, let\'s keep it internal for now."',
                    'Expressive: "But this is such a big win! Everyone should know about it!"'
                ],
                'correct_type': 'expressive',
                'tell_category': 'visibility',
                'tell_explanation': 'The expressive person wants their work recognized and celebrated publicly, showing a need for visibility and acknowledgment.',
                'response_choices': {
                    'A': 'Let\'s keep this internal. No need to make a big deal.',
                    'B': 'I love your enthusiasm! Let\'s share this in our next all-hands meeting and highlight your contribution.',
                    'C': 'Thank you for all your hard work. The team really appreciates you.',
                    'D': 'Before we share, let\'s verify the metrics to ensure the win is substantiated.'
                },
                'correct_response': 'B',
                'response_explanation': 'Expressives need recognition and visibility. Publicly acknowledging their contribution addresses their visibility need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'New Idea Excitement - Expressive',
                'transcript': [
                    'Expressive: "I have the BEST idea for our marketing campaign!"',
                    'Colleague: "What is it?"',
                    'Expressive: "We do a viral TikTok challenge! Everyone will be talking about us!"',
                    'Colleague: "Interesting. We\'d need to run the numbers first."',
                    'Expressive: "Numbers? This is about energy and excitement! Imagine the buzz!"',
                    'Colleague: "I hear you, but we need data before committing."',
                    'Expressive: "You\'re missing the point. This could be huge!"'
                ],
                'correct_type': 'expressive',
                'tell_category': 'visibility',
                'tell_explanation': 'The expressive person is excited about visibility and buzz, prioritizing energy over data.',
                'response_choices': {
                    'A': 'Show me the data first, then we\'ll consider it.',
                    'B': 'This sounds exciting! I love your energy. Let\'s create a quick prototype to showcase the vision, then we can validate with data.',
                    'C': 'Thank you for sharing. How does this idea make you feel?',
                    'D': 'Let\'s analyze the feasibility and ROI of each potential marketing channel systematically.'
                },
                'correct_response': 'B',
                'response_explanation': 'Expressives need their excitement validated first, then you can introduce structure. Recognition before analysis.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Feels Unheard - Expressive',
                'transcript': [
                    'Expressive: "I shared an idea in the meeting, but everyone just moved on."',
                    'Friend: "Maybe they didn\'t understand it."',
                    'Expressive: "They didn\'t even acknowledge it! It was a great idea, and no one noticed."',
                    'Friend: "That must be frustrating."',
                    'Expressive: "It is! I feel invisible. Like my contributions don\'t matter at all."'
                ],
                'correct_type': 'expressive',
                'tell_category': 'visibility',
                'tell_explanation': 'The expressive person feels their contributions are being ignored, threatening their need for visibility and recognition.',
                'response_choices': {
                    'A': 'That\'s frustrating. Let\'s focus on what you can control.',
                    'B': 'I saw your idea and thought it was really creative! Let\'s bring it up again in the next meeting and make sure everyone hears it.',
                    'C': 'I\'m sorry you feel that way. Your feelings are valid.',
                    'D': 'Let\'s analyze why the idea wasn\'t accepted and refine it based on data.'
                },
                'correct_response': 'B',
                'response_explanation': 'Expressives need their ideas acknowledged and given visibility. Publicly recognizing their contribution addresses their need.',
                'is_feels_unheard': True
            },
            
            # RELATIONAL scenarios
            {
                'difficulty': 'easy',
                'scenario_title': 'Team Conflict - Relational',
                'transcript': [
                    'Manager: "There\'s some tension between Team A and Team B."',
                    'Relational: "Oh no, that\'s terrible. Is everyone okay?"',
                    'Manager: "They\'ll be fine, but we need to resolve this."',
                    'Relational: "I\'m worried about how this affects morale. People must be feeling hurt."',
                    'Manager: "We\'ll address it."',
                    'Relational: "Should I reach out to them? I want to make sure everyone feels supported."'
                ],
                'correct_type': 'relational',
                'tell_category': 'belonging',
                'tell_explanation': 'The relational person focuses on people\'s feelings and wants to ensure everyone feels supported and connected.',
                'response_choices': {
                    'A': 'Let\'s just focus on the task. The feelings will sort themselves out.',
                    'B': 'I appreciate your concern for everyone\'s well-being. Let\'s address both the process issue and check in with people individually.',
                    'C': 'Great idea! Reaching out shows you care. People need that connection right now.',
                    'D': 'Before we reach out, let\'s analyze the root causes systematically.'
                },
                'correct_response': 'C',
                'response_explanation': 'Relational types need connection and harmony. Supporting their desire to reach out and care for others addresses their belonging need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Feedback Conversation - Relational',
                'transcript': [
                    'Manager: "I need to give you some feedback on your presentation."',
                    'Relational: "Okay... did I do something wrong?"',
                    'Manager: "No, not wrong. Just some areas to improve."',
                    'Relational: "I really tried hard. I hope I didn\'t let the team down."',
                    'Manager: "You didn\'t let anyone down. Here are the specifics..."',
                    'Relational: "I understand. I just want to make sure everyone knows I care about doing well."'
                ],
                'correct_type': 'relational',
                'tell_category': 'belonging',
                'tell_explanation': 'The relational person worries about team perception and wants reassurance about their relationships and belonging.',
                'response_choices': {
                    'A': 'Focus on improving, not how others see you.',
                    'B': 'Everyone knows you care. This feedback is just to help you grow. The team values you.',
                    'C': 'You didn\'t let anyone down. Your effort is appreciated. Let\'s work through this together.',
                    'D': 'Let\'s review the data points systematically to improve performance.'
                },
                'correct_response': 'C',
                'response_explanation': 'Relational types need reassurance about belonging and being valued. Emphasizing appreciation and working together addresses their need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Feels Unheard - Relational',
                'transcript': [
                    'Relational: "I\'ve been trying to connect with the team, but I feel like an outsider."',
                    'Colleague: "Have you tried joining the project?"',
                    'Relational: "Yes, but it seems like everyone already has their groups. I don\'t fit in anywhere."',
                    'Colleague: "Maybe focus on your own work first."',
                    'Relational: "But I want to be part of the team. I feel so alone here."'
                ],
                'correct_type': 'relational',
                'tell_category': 'belonging',
                'tell_explanation': 'The relational person feels excluded and disconnected, threatening their fundamental need for belonging.',
                'response_choices': {
                    'A': 'Just focus on your work. Connections will happen naturally.',
                    'B': 'You\'re an important part of this team. Let\'s find ways to help you connect. Would you like to grab coffee this week?',
                    'C': 'I understand how lonely that feels. You belong here, and I appreciate you reaching out. Let\'s work together on finding your place.',
                    'D': 'Let\'s analyze team dynamics to identify the optimal integration strategy.'
                },
                'correct_response': 'C',
                'response_explanation': 'Relational types need explicit reassurance about belonging and connection. Offering personal connection and validation addresses their need.',
                'is_feels_unheard': True
            },
            
            # ANALYZER scenarios
            {
                'difficulty': 'easy',
                'scenario_title': 'Uncertain Plan - Analyzer',
                'transcript': [
                    'Manager: "Let\'s launch the new feature next month."',
                    'Analyzer: "What\'s the definition of \'launch\'? Beta or full release?"',
                    'Manager: "Full release, I think."',
                    'Analyzer: "You think? We need specifics. What metrics define success? What\'s the rollback plan?"',
                    'Manager: "We\'ll figure it out as we go."',
                    'Analyzer: "That\'s not sufficient. I need clear parameters and data before committing."'
                ],
                'correct_type': 'analyzer',
                'tell_category': 'accuracy',
                'tell_explanation': 'The analyzer needs precise definitions, metrics, and logical structure before proceeding. Vague plans threaten their need for accuracy.',
                'response_choices': {
                    'A': 'Just trust the process. We\'ll work it out.',
                    'B': 'Good questions. Let me get you the full requirements document with success metrics, timelines, and contingency plans by end of day.',
                    'C': 'I understand you need clarity. How are you feeling about the uncertainty?',
                    'D': 'Let\'s break down the launch into clear phases with defined success criteria for each stage.'
                },
                'correct_response': 'D',
                'response_explanation': 'Analyzers need logical structure, clear definitions, and data. Providing systematic breakdown with criteria addresses their accuracy need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Policy Change - Analyzer',
                'transcript': [
                    'Manager: "We\'re changing our workflow process. Effective Monday."',
                    'Analyzer: "On what basis? What data supports this change?"',
                    'Manager: "Leadership feels it will be better."',
                    'Analyzer: "Feels? That\'s not a valid reason. Show me the analysis, the before/after metrics, the risk assessment."',
                    'Manager: "Sometimes you have to trust leadership."',
                    'Analyzer: "I need logical justification, not feelings. This doesn\'t make sense."'
                ],
                'correct_type': 'analyzer',
                'tell_category': 'accuracy',
                'tell_explanation': 'The analyzer needs data-driven logic, not intuition. Feeling-based decisions threaten their need for accuracy and precision.',
                'response_choices': {
                    'A': 'Leadership knows best. Just follow the new process.',
                    'B': 'You\'re right to ask for data. Here\'s the analysis: efficiency improved 23% in the pilot, error rate decreased 15%, and here\'s the full risk matrix.',
                    'C': 'I understand this feels sudden. How are you feeling about the change?',
                    'D': 'The change is based on three months of data showing improved outcomes. Would you like to review the detailed metrics?'
                },
                'correct_response': 'D',
                'response_explanation': 'Analyzers need logical data and evidence. Providing specific metrics and analysis addresses their accuracy need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Feels Unheard - Analyzer',
                'transcript': [
                    'Analyzer: "I\'ve been pointing out logical flaws in this plan for weeks."',
                    'Colleague: "But the team wants to move forward."',
                    'Analyzer: "That doesn\'t make it right! The data clearly shows problems, but no one listens."',
                    'Colleague: "Maybe you\'re overthinking it."',
                    'Analyzer: "Overthinking? I\'m presenting facts! Why does no one value accuracy anymore?"'
                ],
                'correct_type': 'analyzer',
                'tell_category': 'accuracy',
                'tell_explanation': 'The analyzer feels their logical analysis is being dismissed, threatening their need for accuracy and precision to be valued.',
                'response_choices': {
                    'A': 'Sometimes you need to just go with the flow.',
                    'B': 'I hear your analysis. Let\'s review your data together. What specific issues are you seeing?',
                    'C': 'I understand you feel frustrated. Your perspective is valued.',
                    'D': 'Your logical thinking is crucial. Let\'s examine your data points systematically before we proceed.'
                },
                'correct_response': 'D',
                'response_explanation': 'Analyzers need their logical analysis to be heard and valued. Engaging with their data systematically addresses their accuracy need.',
                'is_feels_unheard': True
            },
            
            # FREE SPIRIT scenarios
            {
                'difficulty': 'easy',
                'scenario_title': 'Rigid Schedule - Free Spirit',
                'transcript': [
                    'Manager: "You need to be at your desk from 9am to 5pm sharp."',
                    'Free Spirit: "Why? I get my work done, just at different times."',
                    'Manager: "That\'s the policy. Everyone follows the same schedule."',
                    'Free Spirit: "But I\'m more creative in the evening. This feels so restrictive."',
                    'Manager: "Rules are rules."',
                    'Free Spirit: "Can\'t we find a way to make this work? I need flexibility."'
                ],
                'correct_type': 'free_spirit',
                'tell_category': 'freedom',
                'tell_explanation': 'The free spirit needs autonomy and flexibility. Rigid rules threaten their need for freedom and self-direction.',
                'response_choices': {
                    'A': 'The policy is clear. Everyone must follow it.',
                    'B': 'I understand you need flexibility. As long as your deliverables are met on time, let\'s find a schedule that works for you.',
                    'C': 'I hear that this feels restrictive. How can we make you more comfortable?',
                    'D': 'Let\'s analyze productivity metrics to determine the optimal schedule structure.'
                },
                'correct_response': 'B',
                'response_explanation': 'Free spirits need autonomy and flexibility. Offering choice within boundaries addresses their freedom need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Micro-management - Free Spirit',
                'transcript': [
                    'Manager: "I need daily updates on your progress. Send me reports every morning."',
                    'Free Spirit: "Daily? That seems excessive. I\'ll let you know when there\'s something important."',
                    'Manager: "I need visibility into what you\'re doing."',
                    'Free Spirit: "But that takes away from my actual work. I feel like I\'m being watched constantly."',
                    'Manager: "It\'s just for coordination."',
                    'Free Spirit: "Can\'t we trust that I\'ll deliver? I need space to work my way."'
                ],
                'correct_type': 'free_spirit',
                'tell_category': 'freedom',
                'tell_explanation': 'The free spirit feels micromanaged and constrained. Excessive oversight threatens their need for autonomy and freedom.',
                'response_choices': {
                    'A': 'Daily updates are non-negotiable. That\'s the process.',
                    'B': 'I trust you\'ll deliver. Let\'s switch to weekly check-ins unless there\'s a blocker. You have autonomy on how you work.',
                    'C': 'I understand you feel constrained. How can we adjust this to feel less intrusive?',
                    'D': 'Based on data, daily check-ins improve coordination by 18%. Let\'s continue with that structure.'
                },
                'correct_response': 'B',
                'response_explanation': 'Free spirits need autonomy and trust. Reducing oversight and giving them control over their process addresses their freedom need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Feels Unheard - Free Spirit',
                'transcript': [
                    'Free Spirit: "Every time I suggest a different approach, it\'s shot down."',
                    'Colleague: "Maybe your ideas don\'t fit the structure."',
                    'Free Spirit: "Why does everything have to be so rigid? There are multiple ways to solve problems."',
                    'Colleague: "The process works. Why change it?"',
                    'Free Spirit: "Because I feel trapped. Like there\'s no room for my creativity or input."'
                ],
                'correct_type': 'free_spirit',
                'tell_category': 'freedom',
                'tell_explanation': 'The free spirit feels their creativity and alternative approaches are being stifled, threatening their need for freedom and autonomy.',
                'response_choices': {
                    'A': 'Sometimes you have to accept the structure that exists.',
                    'B': 'Your creative input is valuable. Let\'s explore your alternative approach. How would you handle this differently?',
                    'C': 'I understand you feel trapped. Your feelings are valid.',
                    'D': 'Let\'s analyze the efficiency metrics of your proposed approach versus the current process.'
                },
                'correct_response': 'B',
                'response_explanation': 'Free spirits need their creativity and alternative approaches valued. Exploring their ideas gives them autonomy and freedom.',
                'is_feels_unheard': True
            },
            
            # GUARDIAN scenarios
            {
                'difficulty': 'easy',
                'scenario_title': 'Risky Proposal - Guardian',
                'transcript': [
                    'Team: "Let\'s try this new untested approach!"',
                    'Guardian: "What are the risks? What happens if it fails?"',
                    'Team: "We\'ll figure it out. It\'s exciting!"',
                    'Guardian: "But we haven\'t tested it. What\'s the backup plan? What protocols are in place?"',
                    'Team: "Don\'t worry so much. Let\'s just try it."',
                    'Guardian: "I can\'t support this without proper safety measures. This feels dangerous."'
                ],
                'correct_type': 'guardian',
                'tell_category': 'safety',
                'tell_explanation': 'The guardian focuses on risks, protocols, and safety measures. Untested approaches without safeguards threaten their need for safety.',
                'response_choices': {
                    'A': 'Sometimes you have to take risks. Trust the process.',
                    'B': 'You\'re right to consider safety. Let\'s run a small pilot first with clear protocols, rollback plans, and risk mitigation strategies.',
                    'C': 'I understand you\'re worried. How are you feeling about this?',
                    'D': 'Let\'s analyze the probability of success and failure modes systematically.'
                },
                'correct_response': 'B',
                'response_explanation': 'Guardians need protocols, safety measures, and risk mitigation. Providing structure with safeguards addresses their safety need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Policy Deviation - Guardian',
                'transcript': [
                    'Manager: "We\'re going to skip the approval process this time. It\'s urgent."',
                    'Guardian: "Skip it? But the policy exists for a reason. What if something goes wrong?"',
                    'Manager: "We\'ll handle it. It\'s fine."',
                    'Guardian: "But we won\'t have documentation. What about liability? What if this sets a precedent?"',
                    'Manager: "You\'re overthinking this."',
                    'Guardian: "I\'m not overthinking. I\'m following protocol. We need proper coverage."'
                ],
                'correct_type': 'guardian',
                'tell_category': 'safety',
                'tell_explanation': 'The guardian insists on following protocols and considering risks. Skipping safety measures threatens their need for proper coverage.',
                'response_choices': {
                    'A': 'Just go with it. We\'ll figure it out later.',
                    'B': 'I understand your concern. Let\'s fast-track the approval process instead of skipping it, maintaining documentation and liability coverage.',
                    'C': 'I hear that this feels risky. How can we make you more comfortable?',
                    'D': 'Let\'s evaluate the risk-benefit ratio and document our decision rationale.'
                },
                'correct_response': 'B',
                'response_explanation': 'Guardians need protocols and risk coverage. Fast-tracking while maintaining safeguards addresses their safety need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Feels Unheard - Guardian',
                'transcript': [
                    'Guardian: "I keep warning about potential issues, but no one listens."',
                    'Colleague: "Maybe you\'re being too cautious."',
                    'Guardian: "Cautious? I\'m trying to prevent problems! Last time we ignored protocols, we had a major incident."',
                    'Colleague: "That was different."',
                    'Guardian: "Was it? I feel like I\'m the only one who cares about safety and proper procedures."'
                ],
                'correct_type': 'guardian',
                'tell_category': 'safety',
                'tell_explanation': 'The guardian feels their safety concerns are being dismissed, threatening their need for protocols and risk management to be valued.',
                'response_choices': {
                    'A': 'You\'re being too cautious. Just trust the process.',
                    'B': 'Your attention to safety is crucial. Let\'s review the protocols together. What specific risks are you seeing?',
                    'C': 'I understand you feel frustrated. Your concern is valid.',
                    'D': 'Let\'s systematically evaluate each potential risk you\'ve identified and determine appropriate mitigation strategies.'
                },
                'correct_response': 'D',
                'response_explanation': 'Guardians need their safety concerns taken seriously with systematic risk evaluation. Engaging with their protocols addresses their safety need.',
                'is_feels_unheard': True
            },
            
            # MIXED/BLENDED scenarios (Medium/Hard difficulty)
            {
                'difficulty': 'medium',
                'scenario_title': 'Deadline Conflict - Driver/Relational Mix',
                'transcript': [
                    'Manager: "We need this done by Friday. Everyone needs to step up."',
                    'Team Member: "But some of us have commitments this week. Can we discuss timing?"',
                    'Manager: "Friday is non-negotiable. We need results now."',
                    'Team Member: "I understand the urgency, but I\'m worried about the team. People are already stressed. Can we find a way that doesn\'t burn everyone out?"',
                    'Manager: "We don\'t have time for feelings. Just get it done."',
                    'Team Member: "I\'ll make it happen, but let\'s also check in with everyone to make sure they\'re okay."'
                ],
                'correct_type': 'relational',
                'tell_category': 'belonging',
                'tell_explanation': 'While acknowledging urgency (Driver element), the person prioritizes team well-being and checking in (Relational dominant).',
                'response_choices': {
                    'A': 'Focus on the deadline. Feelings can wait.',
                    'B': 'Let\'s meet the Friday deadline, and I\'ll set up a quick team check-in to ensure everyone has what they need and feels supported.',
                    'C': 'I appreciate your concern for the team. Let\'s prioritize everyone\'s well-being first.',
                    'D': 'Let\'s analyze the workload distribution to optimize team efficiency.'
                },
                'correct_response': 'B',
                'response_explanation': 'This balances the Driver\'s need for action (meeting deadline) with the Relational\'s need for team connection (check-in).',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Innovation Request - Expressive/Analyzer Mix',
                'transcript': [
                    'Manager: "We need fresh ideas for the product launch."',
                    'Team Member: "I have an exciting concept! It involves interactive social media integration with gamification elements!"',
                    'Manager: "Interesting. What\'s the data behind this?"',
                    'Team Member: "Well, it\'s about creating buzz and engagement. Imagine the visibility!"',
                    'Manager: "But what are the metrics? What\'s the conversion rate? ROI projections?"',
                    'Team Member: "I can pull the data, but you\'re missing the energy and excitement factor. The numbers will follow if we create something amazing."'
                ],
                'correct_type': 'expressive',
                'tell_category': 'visibility',
                'tell_explanation': 'While the person mentions data (Analyzer element), they prioritize excitement, buzz, and visibility (Expressive dominant).',
                'response_choices': {
                    'A': 'Show me the data first, then we\'ll consider it.',
                    'B': 'I love the energy of this idea! Let\'s create a prototype to showcase the vision, and then we\'ll validate with metrics. Your creativity combined with data will make this powerful.',
                    'C': 'Thank you for sharing. How excited are you about this?',
                    'D': 'Let\'s first establish clear metrics and KPIs, then explore creative approaches within those parameters.'
                },
                'correct_response': 'B',
                'response_explanation': 'This validates the Expressive\'s excitement first, then introduces data (which satisfies the Analyzer aspect they mentioned).',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Process Change - Free Spirit/Guardian Mix',
                'transcript': [
                    'Manager: "We\'re updating our workflow. New processes start Monday."',
                    'Team Member: "I appreciate structure, but these new rules feel too rigid. Can we build in some flexibility?"',
                    'Manager: "The process is standardized. Everyone follows the same way."',
                    'Team Member: "But different teams have different needs. I worry about stifling creativity, though I also want to make sure we maintain quality standards."',
                    'Manager: "The process ensures consistency."',
                    'Team Member: "Can we have guidelines instead of strict rules? Something that maintains quality but allows adaptation?"'
                ],
                'correct_type': 'free_spirit',
                'tell_category': 'freedom',
                'tell_explanation': 'While acknowledging the need for quality standards (Guardian element), the person prioritizes flexibility and adaptation (Free Spirit dominant).',
                'response_choices': {
                    'A': 'The process is fixed. Everyone must follow it.',
                    'B': 'Great idea. Let\'s create flexible guidelines with clear quality benchmarks. Teams can adapt the process while maintaining our standards.',
                    'C': 'I understand you need both structure and freedom. How can we make this work for you?',
                    'D': 'Let\'s analyze which process elements are critical versus flexible based on quality metrics.'
                },
                'correct_response': 'B',
                'response_explanation': 'This provides structure (Guardian need) while allowing flexibility (Free Spirit need), with the dominant need being freedom.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Urgent Decision - Driver/Analyzer Mix',
                'transcript': [
                    'Manager: "We need a decision on this vendor by end of day."',
                    'Team Member: "I need to review the contracts and compare metrics first. We can\'t rush into this without proper analysis."',
                    'Manager: "There\'s no time. We need to move now."',
                    'Team Member: "I understand the urgency, but let me give you three options with pros/cons by 3pm. We can decide quickly once we have the data."',
                    'Manager: "3pm might be too late."',
                    'Team Member: "I\'ll have it by 2pm. Three clear options with recommendation. Then we decide."'
                ],
                'correct_type': 'analyzer',
                'tell_category': 'accuracy',
                'tell_explanation': 'While acknowledging urgency (Driver element), the person insists on data and structured analysis before deciding (Analyzer dominant).',
                'response_choices': {
                    'A': 'We don\'t have time. Just pick one.',
                    'B': 'Perfect. I need the options with data by 2pm, then we make the decision. This gives us both speed and accuracy.',
                    'C': 'I understand you need time to analyze. How are you feeling about the pressure?',
                    'D': 'Let\'s systematically evaluate all vendors using our standard criteria matrix before deciding.'
                },
                'correct_response': 'B',
                'response_explanation': 'This satisfies the Analyzer\'s need for data while acknowledging the Driver\'s need for speed and decision-making.',
                'is_feels_unheard': False
            },
            
            # Additional scenarios to reach 36+ total
            {
                'difficulty': 'easy',
                'scenario_title': 'Team Meeting - Expressive',
                'transcript': [
                    'Expressive: "I have so many ideas! This project could be our biggest success yet!"',
                    'Colleague: "Let\'s focus on one thing at a time."',
                    'Expressive: "But imagine the potential! We could be industry leaders!"',
                    'Colleague: "We need to be realistic."',
                    'Expressive: "Realistic? We should aim high! This is exciting!"'
                ],
                'correct_type': 'expressive',
                'tell_category': 'visibility',
                'tell_explanation': 'The expressive person is energized by big vision and recognition, showing a need for visibility and excitement.',
                'response_choices': {
                    'A': 'Let\'s be more realistic. Focus on what\'s achievable.',
                    'B': 'I love your enthusiasm! Let\'s build on this energy. What\'s your top idea that could make us industry leaders?',
                    'C': 'You seem really excited. That\'s wonderful!',
                    'D': 'Before we aim high, let\'s analyze market conditions and feasibility data.'
                },
                'correct_response': 'B',
                'response_explanation': 'Expressives need their excitement validated and channeled. Engaging with their vision addresses their visibility need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Project Planning - Analyzer/Guardian Mix',
                'transcript': [
                    'Manager: "Let\'s start the project next week."',
                    'Team Member: "Before we begin, I need to see the full requirements, risk assessment, success metrics, and contingency plans. What happens if vendor X fails? What if timeline slips?"',
                    'Manager: "We\'ll handle it as we go."',
                    'Team Member: "That\'s not sufficient. I need comprehensive documentation and protocols before committing. This feels risky without proper structure."',
                    'Manager: "You\'re overcomplicating this."',
                    'Team Member: "I\'m ensuring accuracy and safety. We need both data and safeguards before starting."'
                ],
                'correct_type': 'guardian',
                'tell_category': 'safety',
                'tell_explanation': 'While the person asks for data (Analyzer), they emphasize risk, protocols, and safety measures (Guardian dominant).',
                'response_choices': {
                    'A': 'Let\'s just start. We\'ll figure it out.',
                    'B': 'You\'re right to be thorough. Let\'s create the risk assessment and contingency plans together, then review the data before starting.',
                    'C': 'I understand you need structure. How can we make this feel safer?',
                    'D': 'Let\'s systematically document all requirements, risks, and mitigation strategies before proceeding.'
                },
                'correct_response': 'B',
                'response_explanation': 'This addresses both the Guardian\'s need for safety protocols and the Analyzer\'s need for data, with safety being the dominant concern.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Remote Work Policy - Free Spirit',
                'transcript': [
                    'Manager: "Remote work is now limited to two days per week."',
                    'Free Spirit: "Why? I\'ve been productive working from home."',
                    'Manager: "It\'s company policy now."',
                    'Free Spirit: "But that doesn\'t work for my lifestyle. I need flexibility to work when and where I\'m most effective."',
                    'Manager: "Everyone has to follow the same rules."',
                    'Free Spirit: "Can we negotiate? I promise I\'ll deliver results, just give me autonomy over my schedule."'
                ],
                'correct_type': 'free_spirit',
                'tell_category': 'freedom',
                'tell_explanation': 'The free spirit needs autonomy and flexibility. Rigid policies threaten their need for freedom and self-direction.',
                'response_choices': {
                    'A': 'The policy applies to everyone. No exceptions.',
                    'B': 'I understand you need flexibility. Let\'s set clear deliverables and you can work your preferred schedule as long as results are met.',
                    'C': 'I hear that this feels restrictive. How can we make this work for you?',
                    'D': 'Let\'s analyze productivity metrics to determine optimal remote work frequency.'
                },
                'correct_response': 'B',
                'response_explanation': 'Free spirits need autonomy. Focusing on results rather than rules gives them the freedom they need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Client Feedback - Relational',
                'transcript': [
                    'Client: "We\'re not happy with the deliverable."',
                    'Relational: "Oh no, I\'m so sorry. Are you okay? This must be really frustrating."',
                    'Client: "It\'s just not what we needed."',
                    'Relational: "I feel terrible. I really wanted this to work for you. Can we talk about what you need? I want to make sure you feel heard."',
                    'Client: "The timeline was off."',
                    'Relational: "I understand. Let\'s fix this together. Your satisfaction is really important to me."'
                ],
                'correct_type': 'relational',
                'tell_category': 'belonging',
                'tell_explanation': 'The relational person focuses on the client\'s feelings and wants to ensure they feel heard and valued, showing a need for connection.',
                'response_choices': {
                    'A': 'Let\'s just fix the technical issues and move on.',
                    'B': 'I appreciate you sharing this. Let\'s work together to understand exactly what you need and make sure you\'re fully satisfied.',
                    'C': 'I\'m so sorry you\'re feeling this way. Your feelings are completely valid.',
                    'D': 'Let\'s analyze the requirements gap systematically to address the issue.'
                },
                'correct_response': 'B',
                'response_explanation': 'Relational types need connection and to ensure others feel heard. Working together and focusing on satisfaction addresses their belonging need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Strategic Initiative - Driver/Expressive Mix',
                'transcript': [
                    'Manager: "We\'re launching a new initiative."',
                    'Team Member: "Excellent! When do we start? I want to lead this and make it visible. This could be game-changing!"',
                    'Manager: "We need to plan it first."',
                    'Team Member: "Planning is important, but let\'s move fast. I\'m ready to take action now. Plus, if we launch soon, we\'ll get recognition before competitors."',
                    'Manager: "We need stakeholder buy-in."',
                    'Team Member: "I\'ll get buy-in. Give me the green light and I\'ll make this happen. This is our moment to shine!"'
                ],
                'correct_type': 'expressive',
                'tell_category': 'visibility',
                'tell_explanation': 'While showing urgency (Driver), the person emphasizes recognition, visibility, and leading (Expressive dominant).',
                'response_choices': {
                    'A': 'Slow down. We need proper planning first.',
                    'B': 'I love your energy and vision! You\'re perfect to lead this. Let\'s set a 48-hour sprint plan so we can move fast and make this visible. You\'ll get full credit for leading.',
                    'C': 'You seem really excited about this. That\'s great!',
                    'D': 'Before we proceed, let\'s analyze the strategic objectives and success metrics systematically.'
                },
                'correct_response': 'B',
                'response_explanation': 'This validates the Expressive\'s need for visibility and recognition while acknowledging the Driver\'s need for speed and action.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Budget Cut - Guardian',
                'transcript': [
                    'Manager: "We\'re cutting the safety budget by 30%."',
                    'Guardian: "But we need that budget for compliance and risk management. What about our safety protocols?"',
                    'Manager: "We\'ll find efficiencies."',
                    'Guardian: "This concerns me. We have regulatory requirements. What\'s the plan to maintain safety standards? What risks are we accepting?"',
                    'Manager: "We\'ll handle it."',
                    'Guardian: "I need to see the risk mitigation plan. I can\'t support this without proper safety coverage."'
                ],
                'correct_type': 'guardian',
                'tell_category': 'safety',
                'tell_explanation': 'The guardian focuses on safety protocols, compliance, and risk mitigation. Budget cuts to safety threaten their need for proper safeguards.',
                'response_choices': {
                    'A': 'The budget cut is final. We\'ll make it work.',
                    'B': 'I understand your concern. Let\'s review our safety priorities, identify critical protocols that must be maintained, and create a risk mitigation plan before finalizing cuts.',
                    'C': 'I hear that this feels risky. How can we address your concerns?',
                    'D': 'Let\'s analyze which safety measures provide the highest ROI and prioritize those.'
                },
                'correct_response': 'B',
                'response_explanation': 'Guardians need protocols and risk mitigation. Providing structure for maintaining critical safety while addressing budget addresses their safety need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Performance Review - Analyzer',
                'transcript': [
                    'Manager: "You\'re doing well. Keep it up."',
                    'Analyzer: "What does \'doing well\' mean? What are the specific metrics? How do I compare to baseline?"',
                    'Manager: "You\'re meeting expectations."',
                    'Analyzer: "But I need clear definitions. What are the expectations? What\'s the measurement criteria? I need data to improve."',
                    'Manager: "You\'re fine. Don\'t worry about it."',
                    'Analyzer: "Without specific data, I can\'t optimize my performance. I need measurable feedback."'
                ],
                'correct_type': 'analyzer',
                'tell_category': 'accuracy',
                'tell_explanation': 'The analyzer needs precise definitions and metrics. Vague feedback threatens their need for accurate, data-driven information.',
                'response_choices': {
                    'A': 'Just keep doing what you\'re doing. You\'re fine.',
                    'B': 'Good question. Here are your specific metrics: 94% accuracy rate, 15% above target, ranking 2nd in the team. Here\'s the full performance breakdown.',
                    'C': 'I understand you need clarity. How are you feeling about your performance?',
                    'D': 'Let\'s review the performance evaluation criteria and your detailed metrics together.'
                },
                'correct_response': 'D',
                'response_explanation': 'Analyzers need logical structure and specific data. Providing detailed metrics and criteria addresses their accuracy need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Reorganization - Relational/Guardian Mix',
                'transcript': [
                    'Manager: "We\'re restructuring teams next month."',
                    'Team Member: "But what about team relationships? People have built trust. And what happens to our established processes? Will protocols be maintained?"',
                    'Manager: "Change is necessary."',
                    'Team Member: "I understand, but I\'m worried about how this affects people\'s connections and our safety standards. Can we ensure both team cohesion and proper procedures are maintained?"',
                    'Manager: "We\'ll figure it out."',
                    'Team Member: "I need to know people will still feel supported and that our quality protocols won\'t be compromised."'
                ],
                'correct_type': 'relational',
                'tell_category': 'belonging',
                'tell_explanation': 'While mentioning protocols (Guardian element), the person prioritizes team relationships and people feeling supported (Relational dominant).',
                'response_choices': {
                    'A': 'Change happens. People will adapt.',
                    'B': 'I appreciate your concern for both people and processes. Let\'s design the reorganization to preserve team connections and maintain all quality protocols. I\'ll ensure everyone feels supported.',
                    'C': 'I understand you\'re worried about people. Your concern shows you care.',
                    'D': 'Let\'s systematically map current processes and team relationships to ensure continuity in both areas.'
                },
                'correct_response': 'B',
                'response_explanation': 'This addresses both the Relational\'s need for connection and the Guardian\'s need for protocols, with belonging being the primary concern.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Feels Unheard - Expressive',
                'transcript': [
                    'Expressive: "I presented three creative campaign ideas and no one even commented."',
                    'Colleague: "Maybe they\'re still thinking about it."',
                    'Expressive: "It feels like I\'m invisible. I put so much energy into those ideas."',
                    'Colleague: "Ideas come and go. Don\'t take it personally."',
                    'Expressive: "But my work should be recognized! I need to know my contributions matter."'
                ],
                'correct_type': 'expressive',
                'tell_category': 'visibility',
                'tell_explanation': 'The expressive person feels their creative contributions are being ignored, threatening their need for visibility and recognition.',
                'response_choices': {
                    'A': 'Not every idea gets attention. Move on.',
                    'B': 'Your ideas are creative and valuable! Let\'s schedule time to showcase them properly. I want to make sure you get the recognition you deserve.',
                    'C': 'I\'m sorry you feel invisible. Your feelings matter.',
                    'D': 'Let\'s analyze which ideas have the highest potential ROI and focus on those.'
                },
                'correct_response': 'B',
                'response_explanation': 'Expressives need their work recognized and given visibility. Creating a platform to showcase their contributions addresses their need.',
                'is_feels_unheard': True
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Project Kickoff - Driver',
                'transcript': [
                    'Manager: "This project is a priority."',
                    'Driver: "What\'s the deadline? What are my deliverables?"',
                    'Manager: "We\'ll work on the details."',
                    'Driver: "I need specifics now. What\'s the fastest way to completion? What authority do I have to make decisions?"',
                    'Manager: "We\'ll discuss as we go."',
                    'Driver: "I need clear parameters and autonomy to move quickly. Let\'s set this up now."'
                ],
                'correct_type': 'driver',
                'tell_category': 'control',
                'tell_explanation': 'The driver needs clear deliverables, deadlines, and autonomy to proceed quickly, showing a need for control and action.',
                'response_choices': {
                    'A': 'We\'ll figure out details as we go. Just start working.',
                    'B': 'Here\'s what I need from you: deliverable X by date Y. You have full authority on approach A and B. Let\'s move fast.',
                    'C': 'I understand you need clarity. How can we make this clearer?',
                    'D': 'Let\'s systematically break down all deliverables and timelines before starting.'
                },
                'correct_response': 'B',
                'response_explanation': 'Drivers need clear deliverables, deadlines, and autonomy. Providing specifics with decision-making authority addresses their control need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Technology Adoption - Analyzer/Free Spirit Mix',
                'transcript': [
                    'Manager: "We\'re adopting a new software system."',
                    'Team Member: "I need to see the data on efficiency gains and integration requirements first. But I also want flexibility in how we use it. Can we customize workflows?"',
                    'Manager: "It\'s a standard implementation. Everyone uses it the same way."',
                    'Team Member: "Standardization is important for consistency, but I need data to understand it, and I want to adapt it to our team\'s unique needs. Can we have both structure and flexibility?"',
                    'Manager: "The system is what it is."',
                    'Team Member: "I need logical justification for the change and the ability to customize. Both are essential."'
                ],
                'correct_type': 'free_spirit',
                'tell_category': 'freedom',
                'tell_explanation': 'While requesting data (Analyzer element), the person emphasizes customization and flexibility (Free Spirit dominant).',
                'response_choices': {
                    'A': 'The system is standard. Everyone uses it the same way.',
                    'B': 'Great questions. Here\'s the efficiency data showing 25% improvement. Plus, the system has customizable workflows so teams can adapt it while maintaining core functionality.',
                    'C': 'I understand you need both data and flexibility. How can we make this work?',
                    'D': 'Let\'s systematically evaluate the system\'s capabilities and customization options before implementation.'
                },
                'correct_response': 'B',
                'response_explanation': 'This provides the data (Analyzer need) while emphasizing customization flexibility (Free Spirit dominant need).',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Feels Unheard - Analyzer',
                'transcript': [
                    'Analyzer: "I\'ve identified three critical flaws in this approach, but no one will listen."',
                    'Colleague: "Maybe you\'re overanalyzing."',
                    'Analyzer: "I have data! Logic! But everyone goes with their gut feelings instead."',
                    'Colleague: "Sometimes intuition works."',
                    'Analyzer: "Intuition without data is dangerous. I feel like accuracy and logic don\'t matter anymore."'
                ],
                'correct_type': 'analyzer',
                'tell_category': 'accuracy',
                'tell_explanation': 'The analyzer feels their logical analysis is being dismissed in favor of intuition, threatening their need for accuracy and data to be valued.',
                'response_choices': {
                    'A': 'Sometimes you have to trust intuition. Data isn\'t everything.',
                    'B': 'I want to hear your analysis. Your logical thinking is crucial. Let\'s review your data points together.',
                    'C': 'I understand you feel frustrated. Your perspective is valuable.',
                    'D': 'Let\'s systematically examine your identified flaws and the supporting data before making decisions.'
                },
                'correct_response': 'D',
                'response_explanation': 'Analyzers need their logical analysis to be heard and engaged with systematically. Reviewing their data addresses their accuracy need.',
                'is_feels_unheard': True
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Feels Unheard - Guardian',
                'transcript': [
                    'Guardian: "I keep warning about compliance risks, but leadership ignores me."',
                    'Colleague: "Maybe the risks aren\'t as high as you think."',
                    'Guardian: "I\'ve documented everything. There are real liability issues. No one seems to care about proper protocols anymore."',
                    'Colleague: "We\'ve gotten by so far."',
                    'Guardian: "Until we don\'t. I feel like I\'m the only one protecting this organization from serious problems."'
                ],
                'correct_type': 'guardian',
                'tell_category': 'safety',
                'tell_explanation': 'The guardian feels their safety and compliance concerns are being dismissed, threatening their need for protocols and risk management to be valued.',
                'response_choices': {
                    'A': 'We\'ve been fine so far. Don\'t worry so much.',
                    'B': 'Your vigilance is essential. Let\'s review your documented risks together. I want to ensure we have proper safeguards in place.',
                    'C': 'I understand you feel ignored. Your concerns are valid.',
                    'D': 'Let\'s systematically evaluate each compliance risk and establish appropriate mitigation protocols.'
                },
                'correct_response': 'D',
                'response_explanation': 'Guardians need their safety concerns taken seriously with systematic risk evaluation and protocol establishment. Engaging with their documentation addresses their safety need.',
                'is_feels_unheard': True
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Innovation Challenge - Expressive/Free Spirit Mix',
                'transcript': [
                    'Manager: "We need to innovate but stay within guidelines."',
                    'Team Member: "I have exciting new ideas! But I need freedom to experiment. Can we push boundaries while still following core principles?"',
                    'Manager: "We have strict parameters."',
                    'Team Member: "I understand structure, but innovation requires creativity and autonomy. I want to create something amazing that gets recognition, but I need space to explore. Can we find balance?"',
                    'Manager: "We\'ll stick to what works."',
                    'Team Member: "But that limits our potential. Give me creative freedom and I\'ll deliver something groundbreaking that showcases our capabilities!"'
                ],
                'correct_type': 'free_spirit',
                'tell_category': 'freedom',
                'tell_explanation': 'While mentioning recognition (Expressive element), the person prioritizes creative freedom and autonomy to explore (Free Spirit dominant).',
                'response_choices': {
                    'A': 'We need to stick to proven approaches. Innovation is risky.',
                    'B': 'I love your innovative thinking! Let\'s define creative boundaries that give you exploration space while maintaining core guidelines. I\'ll ensure you get credit for the breakthrough.',
                    'C': 'I understand you need both recognition and freedom. How can we make this work?',
                    'D': 'Let\'s analyze successful innovation frameworks to determine optimal creative parameters.'
                },
                'correct_response': 'B',
                'response_explanation': 'This provides structure (boundaries) while giving creative freedom (Free Spirit need) and recognition (Expressive need), with freedom being dominant.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Team Dynamics - Relational/Expressive Mix',
                'transcript': [
                    'Manager: "Team performance is down."',
                    'Team Member: "I\'m worried about morale. People seem disconnected. We should celebrate our wins more and bring the team together. A team event could boost visibility and connection."',
                    'Manager: "Focus on productivity metrics."',
                    'Team Member: "But relationships matter! And people need to feel recognized. Can we work on both team cohesion and highlighting individual contributions? Both are important."',
                    'Manager: "We\'ll address it later."',
                    'Team Member: "Later might be too late. People need to feel valued and connected now."'
                ],
                'correct_type': 'relational',
                'tell_category': 'belonging',
                'tell_explanation': 'While mentioning visibility (Expressive element), the person prioritizes team connection and people feeling valued (Relational dominant).',
                'response_choices': {
                    'A': 'Focus on work. Relationships will improve naturally.',
                    'B': 'You\'re absolutely right. Let\'s schedule a team gathering and create opportunities for both connection and recognition. People need to feel valued.',
                    'C': 'I understand you care about the team. That\'s wonderful.',
                    'D': 'Let\'s analyze team dynamics data to identify improvement strategies.'
                },
                'correct_response': 'B',
                'response_explanation': 'This addresses both the Relational\'s need for connection and the Expressive\'s need for recognition, with belonging being the primary focus.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Feels Unheard - Free Spirit',
                'transcript': [
                    'Free Spirit: "Every time I suggest a creative approach, it\'s shut down."',
                    'Colleague: "Maybe your ideas don\'t fit the process."',
                    'Free Spirit: "The process is too rigid. I feel trapped. Like there\'s no room for my input or creativity."',
                    'Colleague: "Processes exist for a reason."',
                    'Free Spirit: "But I need freedom to contribute. I feel like my unique perspective doesn\'t matter."'
                ],
                'correct_type': 'free_spirit',
                'tell_category': 'freedom',
                'tell_explanation': 'The free spirit feels their creativity and alternative approaches are being stifled, threatening their need for freedom and autonomy.',
                'response_choices': {
                    'A': 'Sometimes you have to accept existing processes.',
                    'B': 'Your creative perspective is valuable! Let\'s find ways to incorporate your ideas. How would you approach this differently?',
                    'C': 'I understand you feel trapped. Your feelings are valid.',
                    'D': 'Let\'s analyze process efficiency to identify where flexibility could be introduced.'
                },
                'correct_response': 'B',
                'response_explanation': 'Free spirits need their creativity valued and given space. Asking for their alternative approach gives them autonomy and freedom.',
                'is_feels_unheard': True
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Quick Decision - Driver',
                'transcript': [
                    'Manager: "We need to decide on vendor X or Y by end of day."',
                    'Driver: "What are the options? Which one gets us results faster?"',
                    'Manager: "They\'re both good. We need to evaluate them."',
                    'Driver: "I don\'t have time for evaluation. Give me the key differences and your recommendation. I\'ll make the call."',
                    'Manager: "But we should discuss..."',
                    'Driver: "Discussion takes time. I need a decision point now. Which one moves us forward fastest?"'
                ],
                'correct_type': 'driver',
                'tell_category': 'control',
                'tell_explanation': 'The driver wants quick options and decision-making authority, showing a need for control and speed.',
                'response_choices': {
                    'A': 'We need to take time to evaluate properly.',
                    'B': 'Here are the key differences: Vendor X (3 days delivery) vs Vendor Y (5 days). Recommendation: Vendor X. You have full authority to decide.',
                    'C': 'I understand you need a decision quickly. How are you feeling about the pressure?',
                    'D': 'Let\'s systematically compare all vendor criteria before deciding.'
                },
                'correct_response': 'B',
                'response_explanation': 'Drivers need options, outcomes, and autonomy to decide. Providing clear recommendation with authority addresses their control need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Product Launch - Expressive',
                'transcript': [
                    'Manager: "We\'re launching the new product line next quarter."',
                    'Expressive: "Excellent! This is going to be huge! Can I lead the launch event? I have amazing ideas for making this visible!"',
                    'Manager: "We\'ll assign roles later."',
                    'Expressive: "But I want to make this memorable. We could do a grand opening with media, influencers, the works! This could really showcase our brand!"',
                    'Manager: "Let\'s keep it simple."',
                    'Expressive: "Simple? This is our moment to shine! Everyone should know about this launch!"'
                ],
                'correct_type': 'expressive',
                'tell_category': 'visibility',
                'tell_explanation': 'The expressive person wants to lead, make the launch visible, and get recognition, showing a need for visibility and excitement.',
                'response_choices': {
                    'A': 'Let\'s keep it low-key. No need for a big production.',
                    'B': 'I love your energy and vision! You\'re perfect to lead this. Let\'s plan a launch event that showcases our brand and your contribution. This is our moment!',
                    'C': 'You seem really excited about this. That\'s great!',
                    'D': 'Before we plan events, let\'s analyze market response data to determine optimal launch strategy.'
                },
                'correct_response': 'B',
                'response_explanation': 'Expressives need recognition and visibility. Giving them leadership and validating their vision addresses their visibility need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Work-Life Balance - Relational',
                'transcript': [
                    'Manager: "We need someone to work this weekend."',
                    'Relational: "But I have family commitments. And I\'m worried about how this affects everyone\'s well-being. People need time to recharge."',
                    'Manager: "It\'s just one weekend."',
                    'Relational: "I know, but I value my relationships with family. And I\'m concerned about team morale if people feel their personal time isn\'t respected."',
                    'Manager: "We\'ll manage."',
                    'Relational: "Can we find a solution that respects people\'s lives? I want to help, but relationships matter to me."'
                ],
                'correct_type': 'relational',
                'tell_category': 'belonging',
                'tell_explanation': 'The relational person prioritizes relationships and people\'s well-being, showing a need for connection and harmony.',
                'response_choices': {
                    'A': 'Work comes first. Family commitments can wait.',
                    'B': 'I understand you value relationships. Let\'s find a solution that works for both work needs and personal commitments. Can we rotate or find volunteers?',
                    'C': 'I appreciate your concern for everyone\'s well-being. That shows you care.',
                    'D': 'Let\'s analyze staffing needs and availability systematically to optimize coverage.'
                },
                'correct_response': 'B',
                'response_explanation': 'Relational types need connection and harmony. Working together to find a solution that respects relationships addresses their belonging need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Data Analysis Request - Analyzer',
                'transcript': [
                    'Manager: "We need to understand why sales are down."',
                    'Analyzer: "I need the complete dataset: sales by region, by product line, by time period. What\'s our baseline? What are the control variables? What\'s the statistical significance?"',
                    'Manager: "Just give me a quick summary."',
                    'Analyzer: "A summary without proper analysis is meaningless. I need to examine correlations, identify confounding variables, and establish causation before making conclusions."',
                    'Manager: "We don\'t have time for all that."',
                    'Analyzer: "Without proper methodology, any conclusion is unreliable. I need comprehensive data and systematic analysis."'
                ],
                'correct_type': 'analyzer',
                'tell_category': 'accuracy',
                'tell_explanation': 'The analyzer insists on comprehensive data, proper methodology, and statistical rigor before conclusions, showing a need for accuracy and precision.',
                'response_choices': {
                    'A': 'Just give us your best guess. We need something now.',
                    'B': 'You\'re right about methodology. Let\'s get you the full dataset with all variables. Can you provide a preliminary analysis in 48 hours, then a comprehensive report next week?',
                    'C': 'I understand you need time to analyze. How are you feeling about the pressure?',
                    'D': 'Let\'s systematically collect all required data points and establish analytical framework before proceeding.'
                },
                'correct_response': 'D',
                'response_explanation': 'Analyzers need systematic methodology and comprehensive data. Establishing analytical framework addresses their accuracy need.',
                'is_feels_unheard': False
            },
            
            # SCENARIOS WHERE "NO" IS THE RIGHT ANSWER (but framed appropriately)
            {
                'difficulty': 'medium',
                'scenario_title': 'Saying No - Driver (Unrealistic Deadline)',
                'transcript': [
                    'Driver: "I need this project completed by end of day tomorrow. I\'ve already committed to the client."',
                    'Manager: "That\'s not possible given our current capacity."',
                    'Driver: "Make it possible. What are my options? I need a solution now."',
                    'Manager: "We can\'t deliver quality work in that timeframe."',
                    'Driver: "Then give me a faster option. I need control of this timeline."',
                    'Manager: "Here are your choices..."'
                ],
                'correct_type': 'driver',
                'tell_category': 'control',
                'tell_explanation': 'The driver needs options and control over the timeline, showing urgency and a need for autonomy in decision-making.',
                'response_choices': {
                    'A': 'I\'m sorry, but that deadline is impossible. We simply can\'t do it.',
                    'B': 'I can\'t deliver the full project tomorrow, but here are your options: Option 1 is a partial delivery (core features) by tomorrow. Option 2 is full delivery in 3 days. Option 3 is I can escalate to get you additional resources if you approve the budget.',
                    'C': 'I understand you\'re feeling pressure. Let\'s talk about why this deadline feels so urgent.',
                    'D': 'We need to analyze the feasibility data before committing to any timeline.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to the original request, Drivers need options and control. Presenting alternatives with clear outcomes respects their control need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Saying No - Expressive (Unrealistic Launch)',
                'transcript': [
                    'Expressive: "I want to launch our new product with a massive celebration! We should invite media, influencers, celebrities - make it huge and visible!"',
                    'Manager: "That sounds exciting, but our budget won\'t support that scale."',
                    'Expressive: "But this is our moment to shine! Everyone will see us! Can\'t we find the budget?"',
                    'Manager: "We have constraints we need to work within."',
                    'Expressive: "I need this to be visible. People need to know about our product!"'
                ],
                'correct_type': 'expressive',
                'tell_category': 'visibility',
                'tell_explanation': 'The expressive person wants maximum visibility and recognition for the launch, showing a need for their work to be seen and celebrated.',
                'response_choices': {
                    'A': 'No, we can\'t afford that. We\'ll do a small internal launch instead.',
                    'B': 'I love your vision for making this visible! While we can\'t do the full celebrity launch now, let\'s create a tiered plan: Phase 1 (this month) is a visible social media campaign highlighting your contribution. Phase 2 (next quarter) can include the bigger launch when budget allows.',
                    'C': 'I understand you want visibility. How important is this to you personally?',
                    'D': 'We need to analyze the ROI of each marketing channel before allocating budget.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no, Expressives need their vision acknowledged and their contribution recognized. Framing alternatives that maintain visibility respects their need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Saying No - Relational (Unreasonable Request)',
                'transcript': [
                    'Relational: "I know you said no personal time off next month, but my best friend is getting married and I need to be there. Relationships matter, right?"',
                    'Manager: "The project deadline conflicts with that week."',
                    'Relational: "But I\'ve been a loyal team member. Friendships are important. Can\'t we work something out that respects relationships?"',
                    'Manager: "This is a critical time for the team."',
                    'Relational: "I don\'t want to let down my friend, and I don\'t want to let down the team either. There must be a way."'
                ],
                'correct_type': 'relational',
                'tell_category': 'belonging',
                'tell_explanation': 'The relational person prioritizes relationships and connection, wanting to honor both personal relationships and team commitments.',
                'response_choices': {
                    'A': 'I\'m sorry, but the project deadline is non-negotiable. You\'ll need to miss the wedding.',
                    'B': 'I understand your friend\'s wedding is important to you, and I value our team relationships too. Here\'s what we can do: If you can get your deliverables done by Thursday and someone can cover Friday, you can take Friday off. This respects both your friendship and our team commitment.',
                    'C': 'I hear that relationships matter deeply to you. How are you feeling about this conflict?',
                    'D': 'We need to analyze project timelines and coverage needs before making exceptions.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when constraints exist, Relational types need their relationships acknowledged. Finding a solution that respects both personal and team relationships addresses their belonging need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Saying No - Analyzer (Insufficient Data Request)',
                'transcript': [
                    'Analyzer: "I need access to all customer data, transaction histories, and internal communications before I can recommend a strategy. Without comprehensive data, any recommendation is invalid."',
                    'Manager: "Some of that data is confidential and can\'t be shared broadly."',
                    'Analyzer: "But how can I make accurate recommendations without complete information? This violates methodological integrity."',
                    'Manager: "We have privacy and security constraints."',
                    'Analyzer: "Without proper data, I cannot provide a logically sound analysis. This doesn\'t make sense."'
                ],
                'correct_type': 'analyzer',
                'tell_category': 'accuracy',
                'tell_explanation': 'The analyzer needs comprehensive data for accurate analysis, showing a need for logical rigor and complete information.',
                'response_choices': {
                    'A': 'I\'m sorry, but we can\'t share that data. You\'ll have to work with what you have.',
                    'B': 'I understand your need for complete data for accurate analysis. While I can\'t provide everything you requested, here\'s what I can give you: anonymized aggregate data sets, statistical summaries of transactions, and a data dictionary explaining all available fields. Plus, I can arrange a session with the data team to answer specific analytical questions.',
                    'C': 'I hear you need more information. How does it feel not having all the data?',
                    'D': 'We need to systematically evaluate which data points are actually required versus desired for the analysis.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to full data access, Analyzers need logical explanation and alternative structured data. Providing systematic alternatives and data dictionaries respects their accuracy need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Saying No - Free Spirit (Rigid Policy)',
                'transcript': [
                    'Free Spirit: "I want to work completely remote, choose my own hours, and skip the standard process. I deliver results, so why do I need rules?"',
                    'Manager: "We have company policies that everyone needs to follow."',
                    'Free Spirit: "But I\'m more creative when I have freedom. These rules feel suffocating. Can\'t we make an exception?"',
                    'Manager: "Standards exist for a reason."',
                    'Free Spirit: "I need autonomy to do my best work. These constraints are limiting my potential."'
                ],
                'correct_type': 'free_spirit',
                'tell_category': 'freedom',
                'tell_explanation': 'The free spirit needs autonomy and flexibility, feeling constrained by rigid policies and rules.',
                'response_choices': {
                    'A': 'I\'m sorry, but the policies apply to everyone. You need to follow them like everyone else.',
                    'B': 'I understand you need flexibility to do your best work. While I can\'t give you complete autonomy on all policies, here\'s what I can offer: flexible hours within core business hours (10am-3pm required), 3 remote days per week, and you can propose alternative processes for your projects that we can evaluate. You\'ll have freedom within these guardrails.',
                    'C': 'I hear that these rules feel restrictive. How can we make you more comfortable?',
                    'D': 'We need to analyze policy effectiveness data before making exceptions.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to complete freedom, Free Spirits need flexibility and autonomy. Offering structured flexibility with clear boundaries respects their freedom need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Saying No - Guardian (Unsafe Practice)',
                'transcript': [
                    'Guardian: "I need to see all safety protocols before we proceed. What\'s the backup plan? What happens if this fails? We need proper safeguards."',
                    'Manager: "We don\'t have time for all that documentation. We\'ll handle issues as they come."',
                    'Guardian: "But that\'s unsafe! We need protocols, risk assessments, and contingency plans. What about compliance? Liability?"',
                    'Manager: "We\'ve done this before. It\'ll be fine."',
                    'Guardian: "Without proper safety measures, I can\'t support this. We need coverage and protocols."'
                ],
                'correct_type': 'guardian',
                'tell_category': 'safety',
                'tell_explanation': 'The guardian insists on safety protocols and risk mitigation, showing a need for proper safeguards and procedures.',
                'response_choices': {
                    'A': 'I\'m sorry, but we need to move fast. The safety documentation will have to wait.',
                    'B': 'I understand your need for proper safety protocols. While we can\'t delay for full documentation now, here\'s what we\'ll do: I\'ll provide the critical safety protocols (emergency procedures, rollback plan, contact list) by end of day. Full documentation can follow, but you\'ll have the essential safeguards to proceed safely.',
                    'C': 'I hear that safety is very important to you. How does this situation make you feel?',
                    'D': 'We need to systematically document all safety requirements before proceeding.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to full documentation delays, Guardians need safety protocols acknowledged. Providing essential safeguards while balancing speed respects their safety need.',
                'is_feels_unheard': False
            },
            
            # MORE SCENARIOS - Variety and difficulty mix
            {
                'difficulty': 'easy',
                'scenario_title': 'Budget Request - Driver',
                'transcript': [
                    'Driver: "I need approval for this budget immediately. Time is money."',
                    'Finance: "We need to review the proposal first."',
                    'Driver: "Review takes time. What\'s the decision process? Who approves? How fast can we move?"',
                    'Finance: "Typically it takes two weeks."',
                    'Driver: "Two weeks? That\'s too slow. What are my options to speed this up?"'
                ],
                'correct_type': 'driver',
                'tell_category': 'control',
                'tell_explanation': 'The driver wants to control the approval timeline and needs options to accelerate the process.',
                'response_choices': {
                    'A': 'Two weeks is our standard process. There\'s no way around it.',
                    'B': 'Here are your options: Option 1 is fast-track review (3 days) if you provide detailed justification. Option 2 is partial approval now for urgent items, rest later. Option 3 is escalate to VP for immediate decision if it\'s critical.',
                    'C': 'I understand waiting feels frustrating. How urgent is this really?',
                    'D': 'We need to analyze the budget proposal against historical spending patterns before approval.'
                },
                'correct_response': 'B',
                'response_explanation': 'Drivers need options and control over timelines. Presenting fast-track alternatives addresses their control need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Team Presentation - Expressive',
                'transcript': [
                    'Expressive: "I want to present our project at the next all-hands meeting. This is a great opportunity to showcase our work and get recognition!"',
                    'Manager: "The all-hands agenda is already full."',
                    'Expressive: "But this is important! People need to see what we\'ve accomplished. Can\'t we make room?"',
                    'Manager: "There are other priorities."',
                    'Expressive: "But visibility matters! This project deserves to be highlighted!"'
                ],
                'correct_type': 'expressive',
                'tell_category': 'visibility',
                'tell_explanation': 'The expressive person wants their work recognized and made visible to the organization.',
                'response_choices': {
                    'A': 'The agenda is set. Maybe next quarter.',
                    'B': 'I love that you want to showcase this! While all-hands is full, let\'s get you visibility another way: We can feature this in the company newsletter this week, and I\'ll propose you for next month\'s all-hands. Your contribution will definitely be recognized.',
                    'C': 'I understand recognition is important to you. How does it feel not being on the agenda?',
                    'D': 'We need to evaluate presentation priority based on project impact metrics.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to the all-hands slot, Expressives need their work acknowledged and given visibility through alternative channels.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Saying No - Expressive (Over Budget)',
                'transcript': [
                    'Expressive: "I have an amazing idea for the product launch! We should rent a venue, get a live band, stream it live - make it an event people will remember forever!"',
                    'Manager: "That sounds exciting, but it\'s way over our budget."',
                    'Expressive: "But the impact! The visibility! This could be the launch everyone talks about. Can\'t we find creative ways to fund it?"',
                    'Manager: "We have financial constraints we need to respect."',
                    'Expressive: "I just know this would be incredible. Everyone would see us!"'
                ],
                'correct_type': 'expressive',
                'tell_category': 'visibility',
                'tell_explanation': 'The expressive person is excited about maximum visibility and recognition, prioritizing impact over budget constraints.',
                'response_choices': {
                    'A': 'No, we simply can\'t afford it. We\'ll do a standard launch instead.',
                    'B': 'Your vision for visibility is fantastic! While we can\'t do the full event now, here\'s what we can create: A live-streamed virtual launch (reaches more people!) with recorded segments from team members. We\'ll promote it heavily and give you full credit. Then we can plan the bigger event for next launch when budget allows.',
                    'C': 'I understand you\'re really excited about this. How important is the live event aspect?',
                    'D': 'We need to analyze the ROI of each launch element against our budget constraints.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to the expensive event, Expressives need their vision validated and their contribution recognized. Offering alternative visibility with credit addresses their need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Saying No - Relational (Team Conflict)',
                'transcript': [
                    'Relational: "I think we should all take time off together to build team bonds. We need stronger relationships and better connection."',
                    'Manager: "We can\'t afford to have the whole team out at once."',
                    'Relational: "But relationships matter more than productivity! People need to feel connected. Can\'t we make an exception for team building?"',
                    'Manager: "Business needs come first."',
                    'Relational: "I\'m worried this will hurt team morale. People need to feel valued and connected."'
                ],
                'correct_type': 'relational',
                'tell_category': 'belonging',
                'tell_explanation': 'The relational person prioritizes team connection and relationships over business operations.',
                'response_choices': {
                    'A': 'I\'m sorry, but we need to maintain operations. Team building will have to wait.',
                    'B': 'I absolutely agree that team connection matters. While we can\'t all take time off together, let\'s find ways to build relationships: We can do half-day team activities on Fridays, schedule regular team lunches, and plan quarterly off-sites. This maintains operations while strengthening connections.',
                    'C': 'I hear that team relationships are really important to you. How does this situation make you feel?',
                    'D': 'We need to analyze the productivity impact of team activities before scheduling.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to full team time off, Relational types need their concern for relationships acknowledged. Offering alternative connection-building approaches respects their belonging need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Saying No - Analyzer (Quick Decision)',
                'transcript': [
                    'Manager: "We need to decide on this vendor today. No time for deep analysis."',
                    'Analyzer: "Today? That\'s insufficient time for proper evaluation. I need to review their financials, security protocols, service history, and compare against alternatives."',
                    'Manager: "We trust our gut on this one."',
                    'Analyzer: "Gut feelings aren\'t data. Without proper analysis, any decision is illogical and risky. I need time for accurate assessment."',
                    'Manager: "The deadline is non-negotiable."',
                    'Analyzer: "Then the decision quality will be compromised. This doesn\'t make sense."'
                ],
                'correct_type': 'analyzer',
                'tell_category': 'accuracy',
                'tell_explanation': 'The analyzer needs comprehensive data and analysis before making decisions, showing a need for logical rigor over intuition.',
                'response_choices': {
                    'A': 'I understand, but we need to decide today. Sometimes you have to go with your gut.',
                    'B': 'I respect your need for accurate analysis. While we can\'t wait for full analysis, here\'s what I can provide: Vendor financials summary, security audit results, and a comparison matrix with three alternatives. You\'ll have structured data to make a logical decision by end of day.',
                    'C': 'I hear that you need more time. How does the pressure feel?',
                    'D': 'We need to systematically evaluate all vendor criteria before deciding.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to extended analysis time, Analyzers need structured data and logical frameworks. Providing compressed but systematic analysis respects their accuracy need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Saying No - Free Spirit (Core Process)',
                'transcript': [
                    'Free Spirit: "I want to completely redesign our workflow. The current process is too rigid. I have creative ideas for how we could do this better."',
                    'Manager: "We need to maintain our core processes for consistency and compliance."',
                    'Free Spirit: "But creativity and innovation require freedom! These processes are stifling. Can\'t we try something new?"',
                    'Manager: "Some processes are non-negotiable for legal reasons."',
                    'Free Spirit: "I feel trapped by all these rules. I need space to innovate."'
                ],
                'correct_type': 'free_spirit',
                'tell_category': 'freedom',
                'tell_explanation': 'The free spirit feels constrained by rigid processes and needs autonomy to innovate creatively.',
                'response_choices': {
                    'A': 'I\'m sorry, but the core processes are mandatory. Everyone needs to follow them.',
                    'B': 'I love your innovative thinking! While we need to keep core compliance processes, here\'s where you have creative freedom: You can redesign the supporting workflows, experiment with collaboration tools, and propose creative approaches for the non-mandatory parts. I\'ll support your innovations within the necessary guardrails.',
                    'C': 'I understand the processes feel restrictive. How can we make this more comfortable?',
                    'D': 'We need to analyze which process elements are legally required versus flexible before making changes.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to changing core processes, Free Spirits need their creativity acknowledged and given innovation space within necessary constraints.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Saying No - Guardian (Innovation Risk)',
                'transcript': [
                    'Manager: "We want to try this new innovative approach. It\'s exciting and could give us an edge!"',
                    'Guardian: "What are the risks? What\'s the rollback plan? Have we tested this? What about compliance and safety protocols?"',
                    'Manager: "We\'ll figure it out as we go. Innovation requires some risk."',
                    'Guardian: "That\'s dangerous! We need proper safeguards, risk assessment, and protocols before trying anything new. What if it fails catastrophically?"',
                    'Manager: "Sometimes you have to take risks to innovate."',
                    'Guardian: "Not without proper safety measures! We need protocols and coverage."'
                ],
                'correct_type': 'guardian',
                'tell_category': 'safety',
                'tell_explanation': 'The guardian prioritizes safety, protocols, and risk mitigation over innovation speed.',
                'response_choices': {
                    'A': 'Innovation requires risk. We\'ll just have to try it and see what happens.',
                    'B': 'I understand your need for proper safeguards. While we want to innovate, let\'s do it safely: We\'ll run a small pilot with full risk assessment, have a rollback plan, maintain all compliance protocols, and monitor closely. Innovation can happen within proper safety frameworks.',
                    'C': 'I hear that safety is really important to you. How does innovation feel risky?',
                    'D': 'We need to systematically evaluate risks and mitigation strategies before proceeding.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to risk-free innovation, Guardians need safety acknowledged and protocols maintained. Framing innovation within safety frameworks respects their need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Resource Request - Driver',
                'transcript': [
                    'Driver: "I need three additional team members by next week to meet this deadline."',
                    'Manager: "We don\'t have budget for new hires right now."',
                    'Driver: "Then what are my options? I need resources to deliver. What can I control here?"',
                    'Manager: "We\'ll have to work with what we have."',
                    'Driver: "That doesn\'t help me. I need clear alternatives and decision points."'
                ],
                'correct_type': 'driver',
                'tell_category': 'control',
                'tell_explanation': 'The driver needs options and control over resources to meet deliverables.',
                'response_choices': {
                    'A': 'I\'m sorry, but there\'s no budget. You\'ll have to make do.',
                    'B': 'I understand you need resources to deliver. While we can\'t hire new staff, here are your options: Option 1 is I can reassign two people from other projects temporarily. Option 2 is we can outsource specific tasks within budget. Option 3 is we can adjust the deadline scope - deliver core features by deadline, rest later.',
                    'C': 'I understand this is stressful. How are you feeling about the resource constraints?',
                    'D': 'We need to analyze resource utilization data before making allocation decisions.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to new hires, Drivers need options and control. Presenting alternative resource solutions addresses their control need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Saying No - Relational/Analyzer Mix (Data Request)',
                'transcript': [
                    'Team Member: "I need access to everyone\'s performance data to help the team improve. Also, I\'m worried about how sharing data might affect team relationships."',
                    'Manager: "Performance data is confidential. We can\'t share individual data."',
                    'Team Member: "But I need accurate information to help people grow, and I want to make sure sharing this won\'t damage team trust. Can we find a way that provides data while protecting relationships?"',
                    'Manager: "Privacy policies prevent sharing individual performance data."',
                    'Team Member: "I understand privacy, but I need aggregate insights to help the team, and I want everyone to feel safe and supported."'
                ],
                'correct_type': 'relational',
                'tell_category': 'belonging',
                'tell_explanation': 'While mentioning data (Analyzer element), the person prioritizes team relationships and ensuring people feel safe and supported (Relational dominant).',
                'response_choices': {
                    'A': 'I\'m sorry, but privacy policies prevent us from sharing any performance data.',
                    'B': 'I appreciate your concern for both accurate insights and team relationships. While we can\'t share individual data, here\'s what I can provide: anonymized aggregate trends, team-wide development themes, and one-on-one sessions where you can help individuals with their own data privately. This maintains privacy while supporting growth.',
                    'C': 'I understand you care about the team. How does not having the data make you feel?',
                    'D': 'We need to systematically evaluate what data can be shared while maintaining privacy compliance.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to individual data sharing, Relational types need their concern for team relationships acknowledged. Providing alternative approaches that protect both data privacy and team connection respects their belonging need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'medium',
                'scenario_title': 'Feature Request - Expressive',
                'transcript': [
                    'Expressive: "I want to add this flashy new feature that will really impress users! It\'ll make us stand out and get attention!"',
                    'Product Manager: "We need to focus on core functionality first."',
                    'Expressive: "But this feature is exciting! It shows our creativity! People will notice us!"',
                    'Product Manager: "We have a roadmap to follow."',
                    'Expressive: "Can\'t we make room for something that gets us visibility and recognition?"'
                ],
                'correct_type': 'expressive',
                'tell_category': 'visibility',
                'tell_explanation': 'The expressive person wants to add features that increase visibility and recognition, prioritizing excitement over roadmap structure.',
                'response_choices': {
                    'A': 'No, we need to stick to the roadmap. Exciting features can come later.',
                    'B': 'I love your creative ideas for visibility! While we need to focus on core features now, let\'s plan this for the next release where we\'ll highlight it prominently. Meanwhile, we can incorporate some visual flair into the current features to make them more noticeable.',
                    'C': 'I understand you want exciting features. How does it feel to have ideas not prioritized?',
                    'D': 'We need to analyze feature priority based on user value metrics.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to immediate implementation, Expressives need their creative ideas acknowledged and given visibility in future planning.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'easy',
                'scenario_title': 'Saying No - Analyzer (Intuition-Based Decision)',
                'transcript': [
                    'Manager: "Let\'s go with this vendor. Our team feels good about them."',
                    'Analyzer: "Feel good? What does that mean? What\'s the data? What are the metrics? How do they compare to alternatives?"',
                    'Manager: "Sometimes you trust your instincts."',
                    'Analyzer: "Instincts aren\'t valid decision criteria. I need logical analysis with data points before we commit. What\'s the methodology?"',
                    'Manager: "We don\'t have time for all that analysis."',
                    'Analyzer: "Without proper evaluation, this decision lacks logical foundation."'
                ],
                'correct_type': 'analyzer',
                'tell_category': 'accuracy',
                'tell_explanation': 'The analyzer needs data-driven logic and methodology, rejecting intuition-based decisions.',
                'response_choices': {
                    'A': 'Sometimes you just have to trust your gut. The team feels good about this.',
                    'B': 'You\'re right that we need data. While we can\'t do a full analysis now, here\'s what I can provide: Vendor comparison matrix with key metrics, references from other clients, and their service level agreements. You\'ll have structured data to evaluate the logical basis for this decision.',
                    'C': 'I understand you need data. How does it feel making decisions without analysis?',
                    'D': 'We need to systematically evaluate all vendors against objective criteria before deciding.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to extended analysis time, Analyzers need structured data and logical frameworks for decisions. Providing systematic evaluation materials respects their accuracy need.',
                'is_feels_unheard': False
            },
            {
                'difficulty': 'hard',
                'scenario_title': 'Saying No - Guardian/Driver Mix (Fast Approval)',
                'transcript': [
                    'Team Member: "We need approval for this initiative immediately. Time is critical. But I also want to make sure we have proper protocols and risk coverage."',
                    'Manager: "Full protocol review takes two weeks. We need to move faster than that."',
                    'Team Member: "I understand urgency, but rushing without safeguards is dangerous. Can we fast-track the essential protocols while maintaining safety standards? I need both speed and proper coverage."',
                    'Manager: "We have to choose: speed or thoroughness."',
                    'Team Member: "There must be a way to have both - rapid approval with core safety protocols."'
                ],
                'correct_type': 'guardian',
                'tell_category': 'safety',
                'tell_explanation': 'While acknowledging urgency (Driver element), the person prioritizes safety protocols and risk coverage (Guardian dominant).',
                'response_choices': {
                    'A': 'We need to choose: either fast approval without protocols, or slow approval with full documentation.',
                    'B': 'I understand you need both speed and safety. Here\'s the solution: We\'ll provide immediate conditional approval with essential safety protocols (emergency procedures, rollback plan, liability coverage) by end of day. Full documentation can follow, but you have the critical safeguards to proceed safely now.',
                    'C': 'I hear you need both speed and safety. How does having to choose feel?',
                    'D': 'We need to systematically prioritize which protocols are critical versus nice-to-have.'
                },
                'correct_response': 'B',
                'response_explanation': 'Even when saying no to full protocol delays, Guardians need safety protocols maintained. Providing essential safeguards quickly addresses both speed (Driver element) and safety (Guardian need).',
                'is_feels_unheard': False
            }
        ]

        # Create scenarios
        created_count = 0
        for scenario_data in scenarios_data:
            scenario, created = Scenario.objects.get_or_create(
                scenario_title=scenario_data['scenario_title'],
                defaults=scenario_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {scenario.scenario_title}'))

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully loaded {created_count} scenarios'))
        self.stdout.write(f'Total scenarios in database: {Scenario.objects.count()}')

